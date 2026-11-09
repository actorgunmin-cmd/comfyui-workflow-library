#!/usr/bin/env python3
"""List the model files each ComfyUI workflow uses and check them on Hugging Face.

Usage: python3 -I audit_models.py <file-or-folder> [--since YYYY-MM-DD] [--list-only]

A repo counts as changed when it has a weight file committed later than a file
the workflows reference, or when a referenced file is gone. With --since, only
commits on or after that date count, and a referenced file that was itself
re-committed since then also counts.

Requests are anonymous and go to the public Hugging Face API only. Exit code is
1 if any repo could not be checked, so a partial result is never mistaken for a
clean one.
"""
import argparse
import collections
import http.client
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

API = 'https://huggingface.co/api/models'
USER_AGENT = 'workflow-model-audit/1.0'
NOTE_TYPES = {'Note', 'MarkdownNote'}
MODEL_RE = re.compile(r'\.(?:safetensors|gguf|ckpt|pt|pth|bin|sft|onnx)$', re.I)
# .bin is left out here: in a repo listing it is mostly tokenizers and training state.
WEIGHT_RE = re.compile(r'\.(?:safetensors|gguf|ckpt|pt|pth|sft|onnx)$', re.I)
HF_URL = re.compile(r'^https?://(?:www\.)?(?:huggingface\.co|hf\.co)/([\w.-]+)/([\w.-]+)/(?:resolve|blob)/[^/]+/([^?#]+)')
NAME_PART = re.compile(r'^[A-Za-z0-9][\w.-]*$')
NEXT_LINK = re.compile(r'<([^>]+)>;\s*rel="next"')
INACTIVE_MODES = {2, 4}  # 2 = muted, 4 = bypassed


class FetchError(Exception):
    def __init__(self, reason, code=None):
        super().__init__(reason)
        self.reason = reason
        self.code = code


def fetch(url):
    """Return (parsed JSON, next page URL or None)."""
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    last = 'network error'
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                link = NEXT_LINK.search(resp.headers.get('Link') or '')
                return json.load(resp), link.group(1) if link else None
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code < 500:
                raise FetchError(f'HTTP {e.code}', e.code)
            last = f'HTTP {e.code}'
            retry_after = e.headers.get('Retry-After') or ''
            time.sleep(min(int(retry_after), 60) if retry_after.isdigit() else 2 ** attempt)
        except (OSError, ValueError, http.client.HTTPException) as e:
            last = type(e).__name__
            time.sleep(2 ** attempt)
    raise FetchError(last)


def fetch_all(url):
    rows = []
    while url:
        page, url = fetch(url)
        rows.extend(page)
    return rows


def norm(name):
    """Cloud import names drop the dots from repo names, so compare without dots or case."""
    return name.replace('.', '').lower()


def base_name(value):
    return re.split(r'[\\/]', value.split('?')[0])[-1]


def parse_prefixed(base):
    """Split a Cloud import name Owner__Repo__file into (owner, repo, file)."""
    parts = urllib.parse.unquote(base).split('__')
    if len(parts) < 3 or not NAME_PART.match(parts[0]) or not NAME_PART.match(parts[1]):
        return None
    return parts[0], parts[1], '__'.join(parts[2:])


def tail_of(base):
    prefixed = parse_prefixed(base)
    return prefixed[2] if prefixed else urllib.parse.unquote(base)


def parse_hf_url(url):
    """Return (owner, repo, path in repo) for a Hugging Face file URL."""
    m = HF_URL.match(url or '')
    return (m.group(1), m.group(2), urllib.parse.unquote(m.group(3))) if m else None


def walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)


def iter_nodes(wf):
    yield from wf.get('nodes') or []
    for sg in (wf.get('definitions') or {}).get('subgraphs') or []:
        yield from sg.get('nodes') or []


def scan_workflow(wf):
    """Return (models, urls): models maps file name to usage, urls maps file name to its HF source."""
    sg_ids = {sg.get('id') for sg in (wf.get('definitions') or {}).get('subgraphs') or []}
    models, urls, declared = {}, {}, set()

    def add_url(name, url):
        parsed = parse_hf_url(url)
        if parsed:
            for key in filter(None, (name, base_name(parsed[2]))):
                urls[key] = parsed
        return parsed

    for model in wf.get('models') or []:
        name = model.get('name') or base_name(model.get('url') or '')
        add_url(name, model.get('url'))
        declared.add(name)

    for node in iter_nodes(wf):
        node_type = node.get('type')
        if node_type in NOTE_TYPES:
            continue
        for source in (node.get('widgets_values'), node.get('widgets_values_named')):
            for text in walk_strings(source):
                value = text.strip()
                if '\n' in value or not MODEL_RE.search(value.split('?')[0]):
                    continue
                add_url(base_name(value), value)
                entry = models.setdefault(base_name(value), {'types': set(), 'active': False})
                if node_type not in sg_ids:
                    entry['types'].add(node_type)
                entry['active'] = entry['active'] or node.get('mode', 0) not in INACTIVE_MODES
        for model in (node.get('properties') or {}).get('models') or []:
            name = model.get('name') or base_name(model.get('url') or '')
            add_url(name, model.get('url'))
            declared.add(name)

    used_tails = {tail_of(name) for name in models}
    for name in declared:
        if name and name not in models and tail_of(name) not in used_tails:
            models[name] = {'types': set(), 'active': True, 'declared_only': True}
    return models, urls


def locate(name, tables):
    """Return (owner, repo, path hint or None, file name), or None if no repo is known."""
    prefixed = parse_prefixed(name)
    tail = tail_of(name)
    for table in tables:
        for key in (name, tail):
            hit = table.get(key)
            if hit and (not prefixed or norm(f'{hit[0]}/{hit[1]}') == norm(f'{prefixed[0]}/{prefixed[1]}')):
                return hit[0], hit[1], hit[2], tail
    return (prefixed[0], prefixed[1], None, tail) if prefixed else None


class Hub:
    """Anonymous Hugging Face lookups, with repo names resolved case- and dot-insensitively."""

    def __init__(self, declared):
        self.declared = {norm(r): r for r in declared}
        self.authors = {}

    def repo_info(self, repo_id):
        owner, repo = repo_id.split('/')
        return fetch(f'{API}/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}')[0]

    def by_author(self, owner, repo_key):
        if owner not in self.authors:
            query = urllib.parse.urlencode({'author': owner, 'limit': 1000})
            self.authors[owner] = fetch_all(f'{API}?{query}')
        return [m['id'] for m in self.authors[owner] if norm(m['id'].split('/')[1]) == repo_key]

    def resolve(self, owner, repo):
        """Return the repo's info, trying the name as written, then the author's repo list."""
        repo_id = self.declared.get(norm(f'{owner}/{repo}'), f'{owner}/{repo}')
        try:
            return self.repo_info(repo_id), None
        except FetchError as e:
            if e.code not in (401, 403, 404):
                raise
            first_error = e
        matches = self.by_author(owner, norm(repo))
        if not matches:
            raise first_error
        note = f'{len(matches)} repos match {owner}/{repo}, using {matches[0]}' if len(matches) > 1 else None
        return self.repo_info(matches[0]), note

    def tree(self, repo_id):
        owner, repo = (urllib.parse.quote(p) for p in repo_id.split('/'))
        return [e for e in fetch_all(f'{API}/{owner}/{repo}/tree/main?recursive=true&expand=true') if e.get('type') == 'file']


def commit_date(entry):
    return (entry.get('lastCommit') or {}).get('date') or ''


def find_in_tree(by_path, hint, file_name):
    """Match by exact path, then by file name in any folder (the newest copy if several)."""
    if hint and hint in by_path:
        return by_path[hint]
    wanted = {file_name.lower(), file_name.replace('__', '/').lower()}
    hits = [e for p, e in by_path.items() if p.lower() in wanted or p.rsplit('/', 1)[-1].lower() == file_name.lower()]
    return max(hits, key=commit_date) if hits else None


def load_workflows(target):
    """Yield (display name, parsed JSON), reporting files that are not UI-format workflows."""
    if os.path.isfile(target):
        paths = [(os.path.basename(target), target)]
    else:
        paths = []
        for folder, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            paths += [(os.path.relpath(os.path.join(folder, f), target), os.path.join(folder, f)) for f in files if f.endswith('.json')]
    named = sorted((unicodedata.normalize('NFC', rel), path) for rel, path in paths)
    for rel, path in named:
        try:
            with open(path, encoding='utf-8') as fh:
                wf = json.load(fh)
        except (OSError, ValueError) as e:
            print(f'skipped {rel}: {type(e).__name__}', file=sys.stderr)
            continue
        if not isinstance(wf, dict) or 'nodes' not in wf:
            print(f'skipped {rel}: not a UI-format workflow', file=sys.stderr)
            continue
        yield rel, wf


def describe_usage(info):
    if info.get('declared_only'):
        return 'declared URL only, no widget uses it'
    kinds = ', '.join(sorted(info['types'])) or 'subgraph'
    return kinds if info['active'] else f'{kinds}; muted or bypassed'


def build_refs(workflows):
    """Print the per-workflow list and group references by repo."""
    folder_urls = {}
    for _rel, _models, urls in workflows:
        for key, value in urls.items():
            folder_urls.setdefault(key, value)

    refs = collections.defaultdict(lambda: collections.defaultdict(set))
    no_repo = collections.defaultdict(set)
    print('## Models per workflow')
    for rel, models, urls in workflows:
        print(f'\n### {rel}  (models: {len(models)})')
        for name in sorted(models):
            ref = locate(name, (urls, folder_urls))
            where = f'{ref[0]}/{ref[1]}' if ref else 'no repo known'
            print(f'  {name}  <- {describe_usage(models[name])}  [{where}]')
            if ref:
                refs[(ref[0], ref[1])][(ref[2], ref[3])].add(rel)
            else:
                no_repo[name].add(rel)
    return refs, no_repo


def check_repo(hub, repo_id, used, since):
    """Compare one repo's tree with the files the workflows reference."""
    by_path = {e['path']: e for e in hub.tree(repo_id)}
    referenced, missing = {}, collections.defaultdict(set)
    for (hint, file_name), users in used.items():
        entry = find_in_tree(by_path, hint, file_name)
        if entry:
            referenced.setdefault(entry['path'], set()).update(users)
        else:
            missing[hint or file_name].update(users)

    dates = {p: commit_date(by_path[p]) for p in referenced}
    newer = []
    for path, entry in by_path.items():
        date = commit_date(entry)
        if path in referenced or not WEIGHT_RE.search(path) or not date or (since and date[:10] < since):
            continue
        older = sorted(p for p, d in dates.items() if d and date > d)
        if older:
            newer.append((date, path, entry.get('size') or 0, older))
    newer.sort(reverse=True)
    updated = sorted(p for p, d in dates.items() if since and d[:10] >= since)
    return {'referenced': referenced, 'dates': dates, 'missing': missing, 'newer': newer, 'updated': updated}


def plural(n):
    return f'{n} workflow' + ('' if n == 1 else 's')


def print_changed(repo_id, info, result, note):
    print(f"\n=== {repo_id}  lastModified={info.get('lastModified')}  gated={info.get('gated')}")
    if note:
        print(f'  note: {note}')
    print('  referenced:')
    for path in sorted(result['referenced'], key=lambda p: (result['dates'][p], p)):
        flag = '  (itself updated in this window)' if path in result['updated'] else ''
        print(f"    {result['dates'][path][:10] or 'no date'}  {path}  [{plural(len(result['referenced'][path]))}]{flag}")
    for name, users in sorted(result['missing'].items()):
        print(f'    MISSING     {name}  [{plural(len(users))}]')
    if result['newer']:
        print('  newer weight files:')
    for date, path, size, older in result['newer']:
        if len(older) == len(result['referenced']) and len(older) > 1:
            label = f'all {len(older)} referenced'
        else:
            label = ', '.join(p.rsplit('/', 1)[-1] for p in older[:3]) + (f' +{len(older) - 3} more' if len(older) > 3 else '')
        print(f'    {date[:10]}  {path}  {size / 1e9:.2f}GB  newer than: {label}')


def audit(refs, no_repo, urls_by_workflow, since):
    declared = {f'{o}/{r}' for urls in urls_by_workflow for o, r, _ in urls.values()}
    hub = Hub(declared)
    merged, failed, notes = {}, {}, {}
    for (owner, repo), used in sorted(refs.items()):
        try:
            info, note = hub.resolve(owner, repo)
        except FetchError as e:
            failed[f'{owner}/{repo}'] = (e.reason, {u for users in used.values() for u in users})
            continue
        slot = merged.setdefault(info['id'], {'info': info, 'used': collections.defaultdict(set)})
        for key, users in used.items():
            slot['used'][key].update(users)
        if note:
            notes[info['id']] = note

    changed, unchanged = [], []
    for i, (repo_id, slot) in enumerate(sorted(merged.items()), 1):
        print(f'checking {i}/{len(merged)} {repo_id}', file=sys.stderr)
        try:
            result = check_repo(hub, repo_id, slot['used'], since)
        except FetchError as e:
            failed[repo_id] = (e.reason, {u for users in slot['used'].values() for u in users})
            continue
        target = changed if result['newer'] or result['missing'] or result['updated'] else unchanged
        target.append((repo_id, slot['info'], result))

    window = f'commits on or after {since}' if since else 'any commit later than the referenced file'
    print(f'\n## Hugging Face check ({window})')
    print(f'\n### Repos changed ({len(changed)})')
    for repo_id, info, result in changed:
        print_changed(repo_id, info, result, notes.get(repo_id))
    print(f'\n### Repos with nothing newer ({len(unchanged)})')
    for repo_id, info, result in unchanged:
        newest = max(result['dates'].values(), default='')[:10] or 'no date'
        print(f"  {repo_id}  lastModified={str(info.get('lastModified'))[:10]}  newest referenced={newest}  files={len(result['referenced'])}")
    print(f'\n### Could not check ({len(failed)})')
    for repo_id, (reason, users) in sorted(failed.items()):
        print(f'  {repo_id}: {reason}  [{plural(len(users))}]')
    print(f'\n### No repo known ({len(no_repo)})')
    for name, users in sorted(no_repo.items()):
        print(f'  {name}  [{plural(len(users))}]')

    newer_count = sum(len(r['newer']) for _i, _x, r in changed)
    missing_count = sum(len(r['missing']) for _i, _x, r in changed)
    print(f'\nSUMMARY repos={len(merged) + len(failed)} changed={len(changed)} unchanged={len(unchanged)} '
          f'newer_files={newer_count} missing_files={missing_count} failed={len(failed)} no_repo={len(no_repo)}')
    return 1 if failed else 0


def main():
    sys.stdout.reconfigure(errors='replace')  # file names may not fit a legacy console code page
    parser = argparse.ArgumentParser(description='List the models ComfyUI workflows use and check them on Hugging Face.')
    parser.add_argument('target', help='workflow JSON file or folder')
    parser.add_argument('--since', metavar='YYYY-MM-DD', help='only count commits on or after this date')
    parser.add_argument('--list-only', action='store_true', help='print the per-workflow list and skip the network')
    args = parser.parse_args()
    if args.since and not re.match(r'^\d{4}-\d{2}-\d{2}$', args.since):
        parser.error('--since must look like YYYY-MM-DD')
    if not os.path.exists(args.target):
        parser.error(f'{args.target} does not exist')

    workflows = []
    for rel, wf in load_workflows(args.target):
        models, urls = scan_workflow(wf)
        workflows.append((rel, models, urls))
    if not workflows:
        parser.error('no UI-format workflow JSON found')

    distinct = {name for _rel, models, _urls in workflows for name in models}
    print(f'# Workflows: {len(workflows)}  distinct model files: {len(distinct)}\n')
    refs, no_repo = build_refs(workflows)
    if args.list_only:
        print(f'\nSUMMARY workflows={len(workflows)} distinct_files={len(distinct)} repos={len(refs)} no_repo={len(no_repo)}')
        return 0
    return audit(refs, no_repo, [urls for _r, _m, urls in workflows], args.since)


if __name__ == '__main__':
    sys.exit(main())

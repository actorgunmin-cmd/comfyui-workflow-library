#!/usr/bin/env python3
"""Scan a folder for things that must not go into a public repo.

Usage: python3 -I check_public.py <file-or-folder> [--deny-file words.txt]

Checks file contents and file names for keys, tokens, email addresses and home
folder paths. --deny-file adds your own private words, one per line (blank
lines and lines starting with # are ignored); they match anywhere in the text,
ignoring case. Keep that file out of the repo.

Findings show only the kind and file:line, never the matched text, so the
output is safe to paste. Exit code: 0 clean, 1 findings, 2 usage error.
"""
import argparse
import collections
import os
import re
import sys
import unicodedata

PLACEHOLDER_USERS = r'(?!(?:you|your-name|user|username|name|me|example|shared)\b)'
EMAIL_IGNORE = re.compile(r'^(?:noreply|no-reply)@|@example\.(?:com|org|net)$|^git@|\.(?:png|jpe?g|webp|gif|svg|safetensors|ckpt|pt|pth)$', re.I)
PLACEHOLDER_VALUE = re.compile(r'(?:your|example|placeholder|changeme|x{4,}|<|\$|\{)', re.I)

PATTERNS = {
    'comfy_api_key': re.compile(r'\bcomfyui-[0-9a-f]{32,}'),
    'huggingface_token': re.compile(r'\bhf_[A-Za-z0-9]{30,}'),
    'sk_style_key': re.compile(r'(?<![\w-])sk-[A-Za-z0-9_-]{24,}'),
    'github_token': re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}'),
    'google_key': re.compile(r'\bAIza[0-9A-Za-z_-]{30,}'),
    'aws_key_id': re.compile(r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b'),
    'slack_token': re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{20,}'),
    'private_key_block': re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    'bearer_token': re.compile(r'\b[Bb]earer\s+(?P<value>[A-Za-z0-9._-]{20,})'),
    'secret_field': re.compile(
        r'(?:api[_-]?key|auth[_-]?token(?:_comfy_org)?|access[_-]?token|client[_-]?secret|password|passwd)'
        r'["\']?\s*[:=]\s*["\'](?P<value>[^"\'\s]{8,})["\']', re.I),
    'email': re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+'),
    'home_path': re.compile(
        r'(?<![\w.:/-])/(?:Users|home)/' + PLACEHOLDER_USERS + r'[\w.-]+'
        r'|(?<![A-Za-z])[A-Za-z]:\\{1,2}(?i:users)\\{1,2}' + PLACEHOLDER_USERS + r'[^\\/"\'\s]+'),
}
SKIP_DIRS = {'.git', '__pycache__'}
SKIP_FILES = {'.DS_Store'}
MAX_ROWS = 50


def nfc(text):
    return unicodedata.normalize('NFC', text)


def load_deny(path):
    with open(path, encoding='utf-8-sig') as fh:
        words = [nfc(line.strip()) for line in fh]
    words = [w for w in words if w and not w.startswith('#')]
    return re.compile('|'.join(re.escape(w) for w in words), re.I) if words else None


def is_real_hit(kind, match):
    if kind == 'email':
        return not EMAIL_IGNORE.search(match.group(0))
    if 'value' in match.groupdict():
        return not PLACEHOLDER_VALUE.match(match.group('value'))
    return True


def find_hits(text, patterns):
    """Yield (kind, offset) for every real match."""
    for kind, rx in patterns.items():
        for match in rx.finditer(text):
            if is_real_hit(kind, match):
                yield kind, match.start()


def list_files(target):
    if os.path.isfile(target):
        return [(os.path.basename(target), target)]
    found = []
    for folder, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name not in SKIP_FILES:
                path = os.path.join(folder, name)
                found.append((nfc(os.path.relpath(path, target)), path))
    return sorted(found)


def main():
    sys.stdout.reconfigure(errors='replace')  # file names may not fit a legacy console code page
    parser = argparse.ArgumentParser(description='Scan a folder for secrets and private details before publishing.')
    parser.add_argument('target', help='file or folder to scan')
    parser.add_argument('--deny-file', help='local text file of private words, one per line')
    args = parser.parse_args()
    if not os.path.exists(args.target):
        parser.error(f'{args.target} does not exist')

    patterns = dict(PATTERNS)
    deny_path = None
    if args.deny_file:
        try:
            deny = load_deny(args.deny_file)
        except (OSError, UnicodeDecodeError) as e:
            parser.error(f'cannot read --deny-file: {type(e).__name__}')
        if deny:
            patterns['deny_word'] = deny
        deny_path = os.path.realpath(args.deny_file)

    def safe_path(rel):
        """A file name can hold the very thing being reported, so mask it before printing."""
        for rx in patterns.values():
            rel = rx.sub('***', rel)
        return rel

    files = list_files(args.target)
    hits = collections.defaultdict(list)
    scanned = unreadable = 0
    for rel, path in files:
        if deny_path and os.path.realpath(path) == deny_path:
            continue
        for kind, _offset in find_hits(rel, patterns):
            hits[kind].append(f'{safe_path(rel)}:(file name)')
        try:
            with open(path, encoding='utf-8') as fh:
                text = nfc(fh.read())
        except (OSError, UnicodeDecodeError):
            unreadable += 1
            continue
        scanned += 1
        for kind, offset in find_hits(text, patterns):
            hits[kind].append(f"{safe_path(rel)}:{text.count(chr(10), 0, offset) + 1}")

    print(f'scanned {scanned} text files, skipped {unreadable} non-text or unreadable, deny words: {"on" if "deny_word" in patterns else "off"}')
    for kind in sorted(hits):
        rows = sorted(set(hits[kind]))
        print(f'\n[{kind}] {len(hits[kind])} hits at {len(rows)} places')
        for row in rows[:MAX_ROWS]:
            print(f'  {row}')
        if len(rows) > MAX_ROWS:
            print(f'  ... {len(rows) - MAX_ROWS} more')
    total = sum(len(v) for v in hits.values())
    print(f'\nRESULT {"CLEAN" if not total else "FOUND " + str(total) + " hits"}')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())

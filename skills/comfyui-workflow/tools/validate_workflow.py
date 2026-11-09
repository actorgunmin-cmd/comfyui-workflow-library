#!/usr/bin/env python3
"""Static checks for ComfyUI workflow JSON files (UI format, with subgraphs).

Usage: python3 -I validate_workflow.py <file-or-folder> [--json report.json]

A clean run proves the file is structurally sound. It does NOT prove the
workflow runs or looks right; only a real Comfy Cloud run can show that.
"""
import json
import os
import re
import sys
import unicodedata

MODEL_RE = re.compile(r'\.(?:safetensors|gguf|ckpt|pt|pth|bin|sft|onnx)$', re.I)
NOTE_TYPES = {'Note', 'MarkdownNote'}
SG_IN, SG_OUT = -10, -20


def norm_links(raw):
    out = {}
    for l in raw or []:
        if isinstance(l, dict):
            out[l['id']] = (l['origin_id'], l['origin_slot'], l['target_id'], l['target_slot'], l.get('type'))
        else:
            out[l[0]] = (l[1], l[2], l[3], l[4], l[5] if len(l) > 5 else None)
    return out


def check_graph(name, nodes, links, sg_inputs, sg_outputs, issues, widen):
    by_id = {}
    for n in nodes:
        if n['id'] in by_id:
            issues.append(('error', name, f"duplicate node id {n['id']}"))
        by_id[n['id']] = n

    def add(sev, msg):
        issues.append((sev, name, msg))

    for lid, (o, os_, t, ts, _ty) in links.items():
        if o == SG_IN:
            if os_ >= sg_inputs:
                add('error', f'link {lid}: subgraph input slot {os_} out of range')
        elif o not in by_id:
            add('error', f'link {lid}: origin node {o} missing')
        else:
            outs = by_id[o].get('outputs') or []
            if os_ >= len(outs):
                add('error', f'link {lid}: origin slot {os_} missing on node {o}')
            elif lid not in (outs[os_].get('links') or []):
                add('error', f'link {lid}: not listed on output of node {o} ({by_id[o].get("type")})')
        if t == SG_OUT:
            if ts >= sg_outputs:
                add('error', f'link {lid}: subgraph output slot {ts} out of range')
        elif t not in by_id:
            add('error', f'link {lid}: target node {t} missing')
        else:
            ins = by_id[t].get('inputs') or []
            if ts >= len(ins):
                add('error', f'link {lid}: target slot {ts} missing on node {t}')
            elif ins[ts].get('link') != lid:
                add('error', f'link {lid}: target node {t} slot {ts} points to {ins[ts].get("link")}')

    for n in nodes:
        for i in n.get('inputs') or []:
            if i.get('link') is not None and i['link'] not in links:
                add('error', f"node {n['id']} ({n.get('type')}) input {i.get('name')} uses unknown link {i['link']}")
        for o in n.get('outputs') or []:
            for lid in o.get('links') or []:
                if lid not in links:
                    add('error', f"node {n['id']} ({n.get('type')}) output {o.get('name')} lists unknown link {lid}")

        wv, named = n.get('widgets_values'), n.get('widgets_values_named')
        if isinstance(named, dict) and isinstance(wv, list):
            pos = {v for v in wv if isinstance(v, str) and MODEL_RE.search(v)}
            nam = {v for v in named.values() if isinstance(v, str) and MODEL_RE.search(v)}
            if pos != nam and (pos or nam):
                add('error', f"node {n['id']} ({n.get('type')}): widgets_values models {sorted(pos)} != named {sorted(nam)}")
            for k, v in named.items():
                if k in ('steps', 'seed', 'noise_seed', 'cfg') and isinstance(v, (int, float)) and v not in wv and n.get('type') not in widen:
                    add('warn', f"node {n['id']} ({n.get('type')}): named {k}={v} not found in widgets_values")

    indeg = {i: 0 for i in by_id}
    adj = {i: [] for i in by_id}
    for o, _os, t, _ts, _ty in links.values():
        if o in by_id and t in by_id:
            adj[o].append(t)
            indeg[t] += 1
    queue = [i for i, d in indeg.items() if d == 0]
    done = 0
    while queue:
        v = queue.pop()
        done += 1
        for w in adj[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    if done != len(by_id):
        add('error', f'cycle among nodes {sorted(i for i, d in indeg.items() if d > 0)[:8]}')

    boxes = []
    for n in nodes:
        pos, size = n.get('pos'), n.get('size')
        if n.get('type') in NOTE_TYPES or not pos or not size:
            continue
        p = list(pos.values()) if isinstance(pos, dict) else pos
        s = list(size.values()) if isinstance(size, dict) else size
        if len(s) < 2:
            continue
        boxes.append((n['id'], p[0], p[1], p[0] + s[0], p[1] + s[1]))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a[1] < b[3] - 2 and b[1] < a[3] - 2 and a[2] < b[4] - 2 and b[2] < a[4] - 2:
                add('warn', f'nodes {a[0]} and {b[0]} overlap')


def check_file(path):
    issues = []
    with open(path, encoding='utf-8') as fh:
        wf = json.load(fh)
    defs = (wf.get('definitions') or {}).get('subgraphs') or []
    sg_ids = {d['id'] for d in defs}
    check_graph('top', wf.get('nodes') or [], norm_links(wf.get('links')), 0, 0, issues, sg_ids)

    order = {d['id']: i for i, d in enumerate(defs)}
    for d in defs:
        label = f"subgraph:{d.get('name') or d['id']}"
        check_graph(label, d.get('nodes') or [], norm_links(d.get('links')),
                    len(d.get('inputs') or []), len(d.get('outputs') or []), issues, sg_ids)
        for n in d.get('nodes') or []:
            if n.get('type') in sg_ids and order[n['type']] > order[d['id']]:
                issues.append(('error', label, f"nested subgraph {n['type']} defined after its parent; the frontend drops its values"))

    known_urls = {}
    used = {}
    all_nodes = list(wf.get('nodes') or []) + [n for d in defs for n in d.get('nodes') or []]
    for n in all_nodes:
        for m in (n.get('properties') or {}).get('models') or []:
            known_urls[m.get('name')] = m.get('url')
        if n.get('type') in NOTE_TYPES:
            continue
        for v in n.get('widgets_values') or [] if isinstance(n.get('widgets_values'), list) else []:
            if isinstance(v, str) and MODEL_RE.search(v):
                used.setdefault(v, n.get('type'))
    for m, t in sorted(used.items()):
        base = m.split('/')[-1]
        tail = base.split('__')[-1]
        if not (m in known_urls or base in known_urls or tail in known_urls):
            issues.append(('info', 'models', f'{m} ({t}) has no properties.models download URL'))

    titles = ' '.join(g.get('title', '') for g in wf.get('groups') or [])
    if defs and not re.search(r'입력', titles):
        issues.append(('info', 'layout', 'no top-level group mentioning 입력'))
    if not any(n.get('type') in NOTE_TYPES for n in all_nodes):
        issues.append(('info', 'layout', 'no MarkdownNote guide'))
    return issues


def main():
    args = [a for a in sys.argv[1:] if a != '--json']
    target = args[0]
    out = None
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
        args = [a for a in args if a != out]
    files = []
    if os.path.isfile(target):
        files = [target]
    else:
        for dp, _dn, fn in os.walk(target):
            files += [os.path.join(dp, f) for f in fn if f.endswith('.json')]
    report = {}
    totals = {'error': 0, 'warn': 0, 'info': 0}
    for f in sorted(files):
        rel = unicodedata.normalize('NFC', os.path.relpath(f, target) if os.path.isdir(target) else os.path.basename(f))
        try:
            iss = check_file(f)
        except Exception as e:  # noqa: BLE001 - report any parse failure per file
            iss = [('error', 'file', f'{type(e).__name__}: {e}')]
        report[rel] = iss
        for s, _a, _b in iss:
            totals[s] += 1
        errs = [i for i in iss if i[0] != 'info']
        print(f"{'OK ' if not any(i[0] == 'error' for i in iss) else 'ERR'} {rel}  error={sum(i[0] == 'error' for i in iss)} warn={sum(i[0] == 'warn' for i in iss)} info={sum(i[0] == 'info' for i in iss)}")
        for s, a, b in errs[:12]:
            print(f'    [{s}] {a}: {b}')
        if len(errs) > 12:
            print(f'    ... {len(errs) - 12} more')
    print('TOTAL', len(files), totals)
    if out:
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1)
    sys.exit(1 if totals['error'] else 0)


if __name__ == '__main__':
    main()

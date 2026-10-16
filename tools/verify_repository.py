#!/usr/bin/env python3
"""Verify the delivered PAT-KG repository offline, without regenerating data."""

import argparse
import ast
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / 'hub_injection'
EXCLUDED_DIRS = {
    '.git', '__pycache__', '.venv', 'venv', '.pytest_cache', '.ruff_cache',
    '.opencode-local', '.vscode', '.idea', '.playwright-cli', 'node_modules',
    'regenerated', '.local-checks',
}
SECRET_NAMES = {'api_key.txt', 'opencode_model.txt', 'opencode_model.original.txt'}
MANIFEST = 'DELIVERY_MANIFEST.json'
PORTABLE = 'PORTABLE_MANIFEST.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def file_record(path):
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


def repository_files():
    """Enumerate release files without descending into Git, caches or secrets."""
    import os

    for directory, folders, names in os.walk(ROOT, followlinks=False):
        base = Path(directory)
        folders[:] = sorted(name for name in folders if name not in EXCLUDED_DIRS
                            and not (base / name).is_symlink())
        for name in sorted(names):
            path = base / name
            if (name in SECRET_NAMES or name == '.env' or name.startswith('.env.')
                    or name in {'.DS_Store', 'Thumbs.db'}
                    or path.suffix.lower() in {'.pyc', '.pyo', '.zip'}
                    or (base == ROOT and name.startswith('snapshot_') and path.suffix == '.json')):
                continue
            require(not path.is_symlink(), f'Symlink not supported in inventory: {path}')
            if path != ROOT / MANIFEST:
                yield path


def check_manifest(base, manifest):
    for name, expected in manifest['files'].items():
        path = (base / name).resolve()
        require(path.is_relative_to(base.resolve()), f'Inventory path escapes its root: {name}')
        require(path.is_file(), f'Missing inventory file: {name}')
        require(file_record(path) == expected, f'Inventory mismatch: {name}')
    return len(manifest['files'])


def check_links(files):
    count = 0
    for path in files:
        if path.suffix != '.md':
            continue
        text = path.read_text(encoding='utf-8-sig')
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
            target = target.strip().strip('<>')
            if re.match(r'[A-Za-z][A-Za-z0-9+.-]*:', target) or target.startswith(('#', '//')):
                continue
            local = unquote(target.split('#', 1)[0])
            if local:
                require((path.parent / local).exists(),
                        f'Broken local link in {path.relative_to(ROOT)}: {target}')
                count += 1
    return count


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def check_delivery():
    manifest = read_json(ROOT / 'injection_manifest.json')
    original = read_json(ROOT / 'original_KG/pat_kg_merged.json')
    graph = read_json(ROOT / 'pat_kg_poisoned_10pct.json')
    for key, name in [('graph', 'pat_kg_merged.json'), ('entity_csv', 'entity_id_value_type.csv')]:
        require(digest(ROOT / 'original_KG' / name) == manifest['input_sha256'][key],
                f'Original input hash mismatch: {name}')
    for name, expected in manifest['source_code_sha256'].items():
        require(digest(PIPELINE / name) == expected, f'Generation source changed: {name}')
    for name, expected in manifest['output_sha256'].items():
        require(digest(PIPELINE / 'outputs' / name) == expected, f'Pipeline output changed: {name}')
    for name in ['pat_kg_poisoned_10pct.json', 'injection_manifest.json', 'hub_nodes.csv',
                 'edge_injection_labels.csv', 'node_injection_labels.csv']:
        require(digest(ROOT / name) == digest(PIPELINE / 'outputs' / name),
                f'Root/pipeline delivery copies differ: {name}')
    require(digest(ROOT / 'display/snapshot_visibility.py') == digest(PIPELINE / 'src/snapshot_visibility.py'),
            'Snapshot adapters differ')
    n = len(original['edges'])
    require((len(original['nodes']), n, len(graph['edges'])) == (7868, 7737, 8511),
            'Unexpected delivered graph counts')
    for field in ['nodes', 'relations', 'questions', 'unresolved_paths']:
        require(graph[field] == original[field], f'Original records changed: {field}')
    require(graph['edges'][:n] == original['edges'], 'Original edge prefix changed')
    require(all(graph['metadata'][k] == v for k, v in original['metadata'].items()),
            'Original metadata changed')
    added = graph['edges'][n:]
    require(len(added) == manifest['actual_injected_edges'] == manifest['target_injected_edges'] == 774,
            'Injection budget mismatch')
    require(all(e.get('edge_origin') == 'synthetic_injection' and e.get('value') == 'fake'
                and e['factual_verification']['status'] == 'unresolved' for e in added),
            'Synthetic construction or factual-status labels changed')
    jsonl = [json.loads(line) for line in
             (PIPELINE / 'outputs/injected_edges.jsonl').read_text(encoding='utf-8').splitlines()]
    require(jsonl == added, 'Injected JSONL does not match appended edges')
    triples = {(e['source'], e['relation'], e['target']) for e in graph['edges']}
    require(len(triples) == len(graph['edges']), 'Duplicate graph triples')
    labels = csv_rows(ROOT / 'edge_injection_labels.csv')
    require(len(labels) == len(graph['edges']), 'Edge label row count mismatch')
    for index, (row, edge) in enumerate(zip(labels, graph['edges'])):
        synthetic = index >= n
        require(int(row['edge_index']) == index
                and all(row[key] == edge[key] for key in ('source', 'relation', 'target'))
                and row['is_synthetic_edge'] == str(int(synthetic))
                and row['synthetic_class'] == ('fake' if synthetic else 'original')
                and row['factual_verification_status'] == ('unresolved' if synthetic else 'not_adjudicated'),
                f'Edge label mismatch at index {index}')
    incoming = Counter(e['target'] for e in added)
    outgoing = Counter(e['source'] for e in added)
    labels = csv_rows(ROOT / 'node_injection_labels.csv')
    nodes = {node['id']: node for node in graph['nodes']}
    require(len(labels) == len(nodes) and {row['qid'] for row in labels} == nodes.keys(),
            'Node label coverage mismatch')
    for row in labels:
        qid = row['qid']
        total = incoming[qid] + outgoing[qid]
        require(row['is_synthetic_node'] == '0' and row['entity_type'] == nodes[qid]['entity_type']
                and int(row['incident_to_synthetic_edge']) == int(total > 0)
                and int(row['synthetic_in_degree']) == incoming[qid]
                and int(row['synthetic_out_degree']) == outgoing[qid]
                and int(row['synthetic_total_degree']) == total, f'Node label mismatch: {qid}')
    require(len(incoming.keys() | outgoing.keys()) == 654, 'Participating-node count mismatch')
    require(sum(row['selected_top_k'] == 'True' for row in csv_rows(ROOT / 'hub_nodes.csv')) == 206,
            'Selected hub count mismatch')
    sys.path.insert(0, str(ROOT / 'display'))
    from snapshot_visibility import snapshot_view

    expected = {'Dec2021': (6784, 7053, 642, 6), 'Dec2023': (6967, 7241, 649, 1),
                'March2024': (7090, 7011, 609, 4)}
    for snapshot, counts in expected.items():
        view = snapshot_view(graph, snapshot)
        actual = (len(view['nodes']), len(view['edges']), sum(e['synthetic'] for e in view['edges']),
                  sum(node['synthetically_activated'] for node in view['nodes']))
        require(actual == counts, f'Snapshot counts changed: {snapshot}')
    return {'nodes': len(nodes), 'original_edges': n, 'synthetic_edges': len(added),
            'edges': len(graph['edges']), 'participating_nodes': 654,
            'new_synthetic_nodes': 0, 'snapshot_adapter_all_three_passed': True,
            'original_graph_and_label_bytes_unchanged': True}


def refresh_manifests(files, checks):
    portable_path = PIPELINE / PORTABLE
    portable = read_json(portable_path)
    portable['inventory_scope'] = 'Current hub_injection directory; excludes this manifest itself.'
    portable['files'] = {p.relative_to(PIPELINE).as_posix(): file_record(p) for p in files
                         if p.is_relative_to(PIPELINE) and p != portable_path}
    portable_path.write_text(json.dumps(portable, indent=2) + '\n', encoding='utf-8', newline='\n')
    delivery = {
        'format': 'pat-kg-repository-v2',
        'inventory_scope': 'Repository files except this manifest, local exports, environments, caches and credentials.',
        'files': {p.relative_to(ROOT).as_posix(): file_record(p) for p in files},
        'checks': checks,
    }
    (ROOT / MANIFEST).write_text(json.dumps(delivery, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-manifests', action='store_true',
                        help='Refresh inventories after validating generation hashes, records and links')
    args = parser.parse_args()
    try:
        files = sorted(repository_files())
        checks = check_delivery()
        syntax_count = 0
        for path in files:
            if path.suffix == '.py':
                ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
                syntax_count += 1
        link_count = check_links(files)
        if args.refresh_manifests:
            refresh_manifests(files, checks)
        delivery = read_json(ROOT / MANIFEST)
        require(set(delivery['files']) == {p.relative_to(ROOT).as_posix() for p in files},
                'Repository inventory incomplete; refresh after reviewing intended changes')
        require(delivery['checks'] == checks, 'Recorded delivery checks differ from current checks')
        checked = check_manifest(ROOT, delivery)
        portable = read_json(PIPELINE / PORTABLE)
        require(set(portable['files']) == {p.relative_to(PIPELINE).as_posix() for p in files
                                          if p.is_relative_to(PIPELINE) and p.name != PORTABLE},
                'Pipeline inventory incomplete')
        for item in portable['required_inputs']:
            require(file_record(ROOT / 'original_KG' / item['filename']) ==
                    {'bytes': item['bytes'], 'sha256': item['sha256']}, 'Portable input requirement mismatch')
        portable_count = check_manifest(PIPELINE, portable)
        print(json.dumps({'passed': True, 'repository_files': checked, 'pipeline_files': portable_count,
                          'python_files_parsed': syntax_count, 'local_markdown_links_checked': link_count,
                          'delivery': checks, 'tests_run': False, 'network_used': False}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
        print(json.dumps({'passed': False, 'error': str(error)}, indent=2), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

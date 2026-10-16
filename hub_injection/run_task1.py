#!/usr/bin/env python3
"""Audit, generate and validate an additive PAT-KG perturbation. Python 3.10+."""
import argparse
import csv
import json
import sys
from pathlib import Path

from src.load_data import load_data, sha256, write_json
from src.compute_degrees import compute_degrees
from src.select_hubs import rank_eligible, initial_k, expand_k, selected_hubs
from src.validate_original import validate_original, qa_positive_triples
from src.generate_candidates import generate_candidates
from src.inject_misinformation import injection_budget, balanced_sample, make_injected_edges, augment_graph
from src.validate_poisoned import validate_poisoned
from src.report_statistics import statistics, write_comparison
from src.export_training_labels import write_training_labels

ROOT = Path(__file__).resolve().parent


def run(graph_path, csv_path, work_dir, ratio='0.10', seed=42, top_k_max=20):
    graph_path, csv_path, work_dir = Path(graph_path).resolve(), Path(csv_path).resolve(), Path(work_dir).resolve()
    outputs, reports = work_dir / 'outputs', work_dir / 'reports'
    for path in (graph_path, csv_path):
        if outputs == path or outputs in path.parents or reports == path or reports in path.parents:
            raise ValueError('Input datasets must live outside generated outputs/reports directories')
    graph, rows, hashes = load_data(graph_path, csv_path)
    audit = validate_original(graph, rows)
    original_stats = statistics(graph)
    outputs.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    write_json(reports / 'original_statistics.json', {**original_stats, 'audit': audit, 'input_sha256': hashes})
    (reports / '01_original_dataset_audit.md').write_text(
        '# Original dataset audit\n\nAll listed checks were executed before candidate generation.\n\n```json\n'
        + json.dumps({'input_sha256': hashes, **audit}, indent=2) + '\n```\n\n'
        + 'The graph is a directed multirelational QA annotation projection, not reconstructed temporal Wikidata.\n\n'
        + '\n\n'.join(f'**{key}**: {graph["metadata"][key]}' for key in
                          ('snapshot_semantics', 'node_snapshot_semantics', 'projection_semantics', 'pairing_policy'))
        + '\n\nFull degree, relation, type and snapshot distributions: original_statistics.json.\n', encoding='utf-8')
    degrees = compute_degrees(graph)
    groups = rank_eligible(graph, degrees)
    sizes = initial_k(groups, top_k_max)
    target = injection_budget(len(graph['edges']), ratio)
    positives = qa_positive_triples(graph)
    history = []
    while True:
        hubs = selected_hubs(groups, sizes)
        candidates, diagnostics = generate_candidates(graph, hubs, positives)
        history.append({'k_by_type': dict(sizes), 'unique_candidates': len(candidates), 'diagnostics': diagnostics})
        if len(candidates) >= target:
            break
        new_sizes = expand_k(groups, sizes)
        if new_sizes == sizes:
            break
        sizes = new_sizes
    chosen = balanced_sample(candidates, min(target, len(candidates)), seed)
    injected = make_injected_edges(graph, chosen)
    config = {'injection_ratio': str(ratio), 'seed': seed, 'top_k_max': top_k_max, 'hub_metric': 'total_degree',
              'rounding': 'decimal_exact_round_half_even', 'sampling': 'round_robin_type_then_relation_seeded_within_buckets',
              'compatibility': 'original_directed_relation_role_and_counterpart_general_type',
              'permutation_scope': 'each_candidate_uses_one_pair_local_transposition_on_both_endpoints'}
    source_files=[p for folder in ('src','tests','tools') for p in (ROOT/folder).glob('*.py')]
    source_files += [ROOT/'run_task1.py',ROOT/'run_tests.py',ROOT/'requirements.txt',ROOT/'config/task1_config.json']
    source_hashes={p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(source_files)}
    manifest = {'configuration': config, 'input_sha256': hashes,
                'source_code_sha256': source_hashes,
                'original_unique_edges': len(graph['edges']), 'target_injected_edges': target,
                'actual_injected_edges': len(injected), 'candidate_count': len(candidates),
                'initial_k_max_is_soft_expansion_limit': True,
                'k_by_type': sizes, 'eligible_counts': {k: len(v) for k, v in groups.items()},
                'expansion_history': history, 'factual_verification': {'verified_false': 0, 'unverified': len(injected)},
                'release_schema_version': '2.0',
                'synthetic_class_counts': {'fake':len(injected)},
                'factual_verification_v2': {'verified_false':0,'verified_true':0,'unresolved':len(injected)},
                'all_original_qa_positive_triples_checked': len(positives),
                'qa_check_limit': 'No second-hop cross-product inference for multiple intermediates; not a factual truth oracle.',
                'status': 'PASS' if len(injected) == target else 'PARTIAL',
                'shortfall_reason': None if len(injected) == target else 'All eligible ranked prefixes exhausted under role, type, QA, uniqueness and self-loop constraints.'}
    poisoned = augment_graph(graph, injected, manifest)
    validation = validate_poisoned(graph, poisoned, hubs, target, require_target=len(injected) == target)
    write_json(outputs / 'pat_kg_poisoned_10pct.json', poisoned)
    with (outputs / 'injected_edges.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
        for edge in injected:
            stream.write(json.dumps(edge, sort_keys=True, ensure_ascii=False) + '\n')
    nodes = {n['id']: n for n in graph['nodes']}
    with (outputs / 'hub_nodes.csv').open('w', encoding='utf-8', newline='') as stream:
        fields = ['qid', 'label', 'entity_type', 'in_degree', 'out_degree', 'total_degree',
                  'rank_within_type', 'selected_top_k', 'eligible_for_type_swap']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for kind, ids in groups.items():
            for rank, qid in enumerate(ids, 1):
                node = nodes[qid]
                writer.writerow({'qid': qid, 'label': ' | '.join(node.get('labels', [])), 'entity_type': kind,
                                 **degrees[qid], 'rank_within_type': rank, 'selected_top_k': rank <= sizes[kind],
                                 'eligible_for_type_swap': True})
    (reports / '02_hub_selection.md').write_text(
        '# Hub selection\n\nOriginal edges only. Total degree = in + out; a self-loop counts twice. '
        'Parallel relations count separately. Ties use lexical QID order. Eligible = true boolean, valid general type, '
        'no quality flags, positive total degree.\n\n'
        'Initial K = min(n, top_k_max, max(2, ceil(0.05*n))) for n >= 2; otherwise 0. '
        'Expansion doubles ranked prefixes deterministically, beyond the initial soft cap if needed.\n\n'
        '| Type | Eligible positive-degree nodes | Selected K |\n|---|---:|---:|\n'
        + '\n'.join(f'| {k} | {len(groups[k])} | {sizes[k]} |' for k in groups)
        + '\n\nThe hub CSV contains all eligible positive-degree ranked nodes; selected_top_k identifies actual hubs. '
        'Full expansion attempts are in injection_manifest.json.\n', encoding='utf-8')
    write_comparison(reports, original_stats, statistics(poisoned), injected, diagnostics)
    manifest['training_labels']=write_training_labels(graph,poisoned,outputs)
    current_hashes = {'graph': sha256(graph_path), 'entity_csv': sha256(csv_path)}
    if current_hashes != hashes:
        raise ValueError('Original file checksum changed during execution')
    # Validate the actual serialized artifact, not just the in-memory object.
    with (outputs / 'pat_kg_poisoned_10pct.json').open(encoding='utf-8') as stream:
        serialized = json.load(stream)
    if serialized != poisoned:
        raise ValueError('Serialized graph differs structurally from generated graph')
    validation = validate_poisoned(graph, serialized, hubs, target, require_target=len(injected) == target)
    validation['serialized_graph_equals_generated_graph'] = True
    validation['original_input_checksums_unchanged'] = current_hashes == hashes
    manifest['output_sha256'] = {p.name: sha256(p) for p in sorted(outputs.iterdir())
                                 if p.name in {'pat_kg_poisoned_10pct.json', 'injected_edges.jsonl', 'hub_nodes.csv',
                                               'node_injection_labels.csv','edge_injection_labels.csv'}}
    write_json(outputs / 'injection_manifest.json', manifest)
    write_json(reports / 'validation_results.json', validation)
    return {'status': manifest['status'], 'nodes': len(graph['nodes']), 'original_edges': len(graph['edges']),
            'injected_edges': len(injected), 'total_edges': len(poisoned['edges']), 'candidates': len(candidates),
            'expansion_rounds': len(history) - 1, 'checks_passed': len(validation['checks'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph', type=Path, default=ROOT.parents[1] / 'pat_kg_merged.json')
    parser.add_argument('--entities', type=Path, default=ROOT.parents[1] / 'entity_id_value_type.csv')
    parser.add_argument('--work-dir', type=Path, default=ROOT)
    parser.add_argument('--injection-ratio', default='0.10')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--top-k-max', type=int, default=20)
    parser.add_argument('--hub-metric', choices=['total_degree'], default='total_degree')
    args = parser.parse_args()
    try:
        result = run(args.graph, args.entities, args.work_dir, args.injection_ratio, args.seed, args.top_k_max)
    except (ValueError, KeyError, TypeError, OSError, ArithmeticError) as error:
        parser.exit(2, f'Task 1 failed: {error}\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 3


if __name__ == '__main__':
    sys.exit(main())

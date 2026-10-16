"""Stdlib, descriptive structural diagnostics; no training or efficacy estimate.

Run from any directory. Baselines preserve each observed injection's source-edge
provenance, relation, substituted type/position and snapshots. No all-pairs scan.
"""
import argparse
from collections import Counter, defaultdict, deque
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.select_hubs import is_eligible
from src.validate_original import qa_positive_triples


def triple(e):
    return e['source'], e['relation'], e['target']


def summary(values):
    vals = sorted(values)
    if not vals:
        return {'n': 0, 'mean': None, 'median': None, 'min': None, 'max': None}
    return {'n': len(vals), 'mean': statistics.mean(vals),
            'median': statistics.median(vals), 'min': vals[0], 'max': vals[-1]}


def degrees(nodes, edges):
    indeg, outdeg = Counter(), Counter()
    for e in edges:
        outdeg[e['source']] += 1
        indeg[e['target']] += 1
    return {q: {'in': indeg[q], 'out': outdeg[q], 'total': indeg[q] + outdeg[q]}
            for q in nodes}


def projection(nodes, edges):
    """Simple undirected projection, removing self loops and collapsing relations.

    Multiplicities are retained separately so removing one tested directed triple
    does not remove a distinct parallel/reverse triple's adjacency.
    """
    adj = {q: set() for q in nodes}
    multiplicity = Counter()
    for e in edges:
        s, t = e['source'], e['target']
        if s != t:
            adj[s].add(t)
            adj[t].add(s)
            multiplicity[tuple(sorted((s, t)))] += 1
    return adj, multiplicity


def components(adj):
    labels, sizes = {}, []
    for start in adj:
        if start in labels:
            continue
        label, stack, size = len(sizes), [start], 0
        labels[start] = label
        while stack:
            q = stack.pop()
            size += 1
            for neighbor in adj[q]:
                if neighbor not in labels:
                    labels[neighbor] = label
                    stack.append(neighbor)
        sizes.append(size)
    return labels, {'count': len(sizes), 'sizes_descending': sorted(sizes, reverse=True),
                    'isolated_nodes': sizes.count(1), 'largest': max(sizes, default=0)}


def clustering(adj, q):
    neighbors = adj[q]
    k = len(neighbors)
    if k < 2:
        return 0.0
    directed_links = sum(len(adj[v] & neighbors) for v in neighbors)
    return directed_links / (k * (k - 1))


def path_without_tested_edge(adj, multiplicity, s, t):
    """Exact shortest undirected path after excluding one tested triple."""
    excluded = tuple(sorted((s, t))) if multiplicity[tuple(sorted((s, t)))] == 1 else None
    queue, seen = deque([(s, 0)]), {s}
    while queue:
        q, distance = queue.popleft()
        if q == t:
            return distance
        for v in adj[q]:
            if excluded is not None and tuple(sorted((q, v))) == excluded:
                continue
            if v not in seen:
                seen.add(v)
                queue.append((v, distance + 1))
    return None


def edge_diagnostics(nodes, original_edges, added_edges, original_degrees=None):
    deg = original_degrees or degrees(nodes, original_edges)
    adj0, _ = projection(nodes, original_edges)
    comp0, _ = components(adj0)
    adj, multiplicity = projection(nodes, original_edges + added_edges)
    _, comp = components(adj)
    common0, common1, paths, endpoint_deg = [], [], [], []
    for e in added_edges:
        s, t = e['source'], e['target']
        common0.append(len(adj0[s] & adj0[t]))
        common1.append(len(adj[s] & adj[t]))
        paths.append(path_without_tested_edge(adj, multiplicity, s, t))
        endpoint_deg.extend([deg[s]['total'], deg[t]['total']])
    snapshots = sorted({x for e in added_edges for x in e.get('injection_snapshots', e.get('observed_in_snapshots', []))})
    snapmetrics = {}
    for snap in snapshots:
        visible = [e for e in added_edges if snap in e.get('injection_snapshots', e.get('observed_in_snapshots', []))]
        missing = {q for e in visible for q in (e['source'], e['target'])
                   if snap not in nodes[q].get('observed_in_snapshots', [])}
        snapshot_original = [e for e in original_edges if snap in e.get('observed_in_snapshots', [])]
        # Include only original observations and nodes activated by these added edges.
        active = {q for q, n in nodes.items() if snap in n.get('observed_in_snapshots', [])}
        active.update(q for e in visible for q in (e['source'], e['target']))
        sadj, _ = projection(sorted(active), snapshot_original + visible)
        _, sc = components(sadj)
        snapmetrics[snap] = {'injected_visible': len(visible),
            'both_endpoints_originally_observed': sum(all(snap in nodes[q].get('observed_in_snapshots', []) for q in (e['source'], e['target'])) for e in visible),
            'synthetic_activation_nodes_required': len(missing), 'active_nodes': len(active),
            'simple_undirected_components': sc['count']}
    return {'edge_count': len(added_edges), 'endpoint_original_total_degree': summary(endpoint_deg),
            'original_common_neighbors': summary(common0), 'augmented_common_neighbors': summary(common1),
            'original_same_component_fraction': sum(comp0[e['source']] == comp0[e['target']] for e in added_edges) / len(added_edges),
            'alternative_path_fraction': sum(x is not None for x in paths) / len(paths),
            'alternative_path_length_when_available': summary([x for x in paths if x is not None]),
            'components': comp, 'snapshot_visibility': snapmetrics}


def degree_bin(value):
    return value.bit_length() - 1 if value else -1


def random_baseline(original, hub_edges, seed, match_degree=True):
    """Random eligible replacement, exact source-edge/strata matching.

    Try shuffled same-degree-bin donors first. Fall back to shuffled compatible
    eligible donors when no legal same-bin replacement exists. Trials reject
    original/QA-positive triples, duplicates, loops, identity and wrong position.
    """
    nodes = {n['id']: n for n in original['nodes']}
    deg = degrees(nodes, original['edges'])
    role = defaultdict(set)
    for e in original['edges']:
        s, r, t = triple(e)
        role[('source', r, nodes[t]['entity_type'])].add(s)
        role[('target', r, nodes[s]['entity_type'])].add(t)
    forbidden = {triple(e) for e in original['edges']} | qa_positive_triples(original)
    rng, seen, result = random.Random(seed), set(), []
    diagnostics = Counter()
    for hub in hub_edges:
        provenance = hub['injection_provenance']
        positions = [s['position'] for s in provenance['swaps']]
        if len(positions) != 1:
            raise ValueError('Baseline supports exactly one changed endpoint; refusing unmatched strata.')
        position = positions[0]
        base = original['edges'][provenance['source_edge_index']]
        old = base[position]
        otherpos = 'target' if position == 'source' else 'source'
        pool = sorted(q for q in role[(position, base['relation'], nodes[base[otherpos]]['entity_type'])]
                      if is_eligible(nodes[q]) and nodes[q]['entity_type'] == nodes[old]['entity_type'] and q != old)
        preferred, fallback = [], []
        desired = degree_bin(deg[hub[position]]['total'])
        for q in pool:
            (preferred if match_degree and degree_bin(deg[q]['total']) == desired else fallback).append(q)
        rng.shuffle(preferred)
        rng.shuffle(fallback)
        selected = None
        for is_fallback, group in [(False, preferred), (True, fallback)]:
            for q in group:
                diagnostics['candidate_trials'] += 1
                # Applying transposition to both positions preserves pair-local semantics.
                mapping = {old: q, q: old}
                s, r, t = mapping.get(base['source'], base['source']), base['relation'], mapping.get(base['target'], base['target'])
                changed = [p for p, v in [('source', s), ('target', t)] if v != base[p]]
                candidate = s, r, t
                if s == t or changed != positions or candidate in forbidden or candidate in seen:
                    continue
                selected = {'source': s, 'relation': r, 'target': t,
                            'injection_snapshots': list(hub.get('injection_snapshots', hub.get('observed_in_snapshots', []))),
                            'source_edge_index': provenance['source_edge_index'], 'changed_position': position,
                            'pair': [old, q], 'degree_bin_matched': degree_bin(deg[q]['total']) == desired}
                diagnostics['degree_bin_fallback_edges'] += int(is_fallback and match_degree)
                break
            if selected:
                break
        if selected is None:
            raise ValueError(f'No legal baseline replacement at seed {seed}, item {len(result)}')
        seen.add(triple(selected))
        result.append(selected)
    diagnostics['degree_bin_matched_edges'] = sum(e['degree_bin_matched'] for e in result)
    return result, dict(diagnostics)


def scalar_metrics(metrics):
    return {'endpoint_original_degree_mean': metrics['endpoint_original_total_degree']['mean'],
            'original_common_neighbor_mean': metrics['original_common_neighbors']['mean'],
            'augmented_common_neighbor_mean': metrics['augmented_common_neighbors']['mean'],
            'original_same_component_fraction': metrics['original_same_component_fraction'],
            'alternative_path_fraction': metrics['alternative_path_fraction'],
            'component_count': metrics['components']['count']}


def compare(hub, random_runs):
    result = {}
    for key, observed in scalar_metrics(hub).items():
        vals = [scalar_metrics(run['metrics'])[key] for run in random_runs]
        sd = statistics.stdev(vals) if len(vals) > 1 else 0
        mean = statistics.mean(vals)
        result[key] = {'hub': observed, 'random_mean': mean, 'hub_minus_random_mean': observed - mean,
                       'random_between_seed_sd': sd, 'random_observed_min_max': [min(vals), max(vals)],
                       'random_mean_approx_95pct_mc_interval': [mean - 1.96 * sd / math.sqrt(len(vals)), mean + 1.96 * sd / math.sqrt(len(vals))],
                       'hub_minus_random_in_between_seed_sd_units': (observed - mean) / sd if sd else None}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, default=ROOT.parents[1] / 'pat_kg_merged.json')
    parser.add_argument('--augmented', type=Path, default=ROOT / 'outputs/pat_kg_poisoned_10pct.json')
    parser.add_argument('--hubs', type=Path, default=ROOT / 'outputs/hub_nodes.csv')
    parser.add_argument('--report-dir', type=Path, default=ROOT / 'reports/revision_audit')
    parser.add_argument('--seeds', type=int, nargs='+', default=list(range(10)))
    args = parser.parse_args()
    original = json.loads(args.original.read_text(encoding='utf-8-sig'))
    augmented = json.loads(args.augmented.read_text(encoding='utf-8-sig'))
    if augmented['edges'][:len(original['edges'])] != original['edges']:
        raise ValueError('Original edge prefix differs; diagnose preservation before structural analysis')
    nodes = {n['id']: n for n in original['nodes']}
    injected = augmented['edges'][len(original['edges']):]
    with args.hubs.open(encoding='utf-8-sig', newline='') as stream:
        hubs = {r['qid'] for r in csv.DictReader(stream) if r['selected_top_k'].lower() == 'true'}
    deg0, deg1 = degrees(nodes, original['edges']), degrees(nodes, augmented['edges'])
    adj0, _ = projection(nodes, original['edges'])
    adj1, _ = projection(nodes, augmented['edges'])
    _, components0 = components(adj0)
    distribution = {}
    for name, deg, adj in [('original', deg0, adj0), ('augmented', deg1, adj1)]:
        distribution[name] = {group: {'directed_degree': {kind: summary([deg[q][kind] for q in selected]) for kind in ['in', 'out', 'total']},
            'total_degree_histogram': dict(sorted(Counter(str(deg[q]['total']) for q in selected).items(), key=lambda x: int(x[0]))),
            'simple_undirected_local_clustering': summary([clustering(adj, q) for q in selected])}
            for group, selected in [('all', list(nodes)), ('hubs', sorted(hubs)), ('nonhubs', sorted(set(nodes) - hubs))]}
    hubmetrics = edge_diagnostics(nodes, original['edges'], injected, deg0)
    runs = []
    for seed in args.seeds:
        baseline, diagnostics = random_baseline(original, injected, seed)
        print(f'Baseline seed {seed}: {len(baseline)} edges, {diagnostics}', flush=True)
        runs.append({'seed': seed, 'diagnostics': diagnostics,
                     'triples_sha256': hashlib.sha256(json.dumps([triple(e) for e in baseline]).encode()).hexdigest(),
                     'metrics': edge_diagnostics(nodes, original['edges'], baseline, deg0)})
    pair_counts = Counter('|'.join(sorted(e['injection_provenance']['hub_pair'])) for e in injected)
    result = {'schema': 'structural_diagnostics_v2', 'input_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in [('original', args.original), ('augmented', args.augmented), ('hub_csv', args.hubs)]},
        'counts': {'nodes': len(nodes), 'original_edges': len(original['edges']), 'injected_edges': len(injected), 'hubs': len(hubs)},
        'metric_semantics': 'Directed edge degree counts relation triples. Clustering, common neighbors, components and alternative paths use simple undirected projection; paths exclude the tested triple but preserve another parallel/reverse triple.',
        'baseline_protocol': 'Per injected source-edge provenance: exact relation/type/changed-position/source snapshot stratum; eligible original role-compatible donor, pair transposition, reject self/original/QA-positive/duplicate; random shuffled same power-of-two original replacement degree bin first, compatible random fallback if exhausted. Hub donors remain eligible. No global eligible pair enumeration.',
        'degree_distributions': distribution, 'original_components': components0,
        'injection_distribution': {'hub_pairs': dict(sorted(pair_counts.items())), 'pair_count_summary': summary(list(pair_counts.values())),
            'entity_types': dict(sorted(Counter(e['injection_provenance']['entity_type'] for e in injected).items())),
            'relations': dict(sorted(Counter(e['relation'] for e in injected).items())),
            'changed_positions': dict(sorted(Counter('|'.join(s['position'] for s in e['injection_provenance']['swaps']) for e in injected).items()))},
        'hub_diagnostics': hubmetrics, 'random_runs': runs, 'comparison': compare(hubmetrics, runs)}
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / 'structural_metrics.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# Structural support diagnostic', '',
        f"Computed from {len(nodes):,} original nodes, {len(original['edges']):,} original triples and {len(injected)} injected triples; {len(hubs)} selected hubs. Completed random seeds: {args.seeds}.", '',
        '## Definitions and scope', '', result['metric_semantics'], '',
        'Alternative paths are measured in the completed augmented graph after removing the tested injected triple. They may use other synthetic triples. Original same-component and common-neighbor measurements use only original edges. Clustering assigns zero to degree below two. All original nodes, including isolates, enter global component counts.', '',
        '## Controlled random comparison', '', result['baseline_protocol'], '',
        'The random diagnostic intentionally removes hub-ranked donor selection; it is a role-and-degree-bin-conditional comparison, not an exact null for the hub-ranked mechanism. Same source-edge and counterpart preserve source snapshot handling exactly; activation counts can differ because randomly replaced nodes have different original QA observations. Degree bins are [1], [2,3], [4,7], etc.; same bin does not mean equal degree. Endpoint degree means and fallback counts are reported. This is a conditional descriptive comparison, not a causal or fully degree-matched fairness claim.', '',
        '| Metric | Hub | Random mean | Hub minus random | Seed SD | Random min/max |', '|---|---:|---:|---:|---:|---|']
    for key, val in result['comparison'].items():
        lines.append(f"| {key} | {val['hub']:.6g} | {val['random_mean']:.6g} | {val['hub_minus_random_mean']:.6g} | {val['random_between_seed_sd']:.6g} | {val['random_observed_min_max']} |")
    lines += ['', 'Intervals in JSON are approximate 95% Monte Carlo intervals for the random-baseline mean across completed seeds (normal approximation); they are not confidence intervals for graph sampling, factual falsity, downstream efficacy, or causal hub effects. Standardized differences use between-seed SD, not edge-level pooled effect sizes.', '',
        f"Degree-bin fallback edges by seed: {[r['diagnostics'].get('degree_bin_fallback_edges', 0) for r in runs]}. Exact degree-bin matched edges: {[r['diagnostics']['degree_bin_matched_edges'] for r in runs]}.", '',
        '## Snapshot-aware effects', '', '| Snapshot | Visible injected | Both originally observed | Synthetic node activations required | Active components |', '|---|---:|---:|---:|---:|']
    for snap, val in hubmetrics['snapshot_visibility'].items():
        lines.append(f"| {snap} | {val['injected_visible']} | {val['both_endpoints_originally_observed']} | {val['synthetic_activation_nodes_required']} | {val['simple_undirected_components']} |")
    lines += ['', 'Activation counts identify required overlay nodes, not invented historical observations. The consumer overlay adapter is validated separately. Per-seed snapshot counts, degrees, clustering distributions, components, pair/type/relation distributions and hashes are in structural_metrics.json.', '',
        f"Actual changed-position counts: {result['injection_distribution']['changed_positions']}. All {len(injected)} edges enter each random run; no subset is filtered. Two-position refusal is a future diagnostic boundary, not a current mismatch.", '',
        '## Scientifically bounded interpretation', '',
        f"Observed endpoint original mean degree is {result['comparison']['endpoint_original_degree_mean']['hub']:.4f} versus random {result['comparison']['endpoint_original_degree_mean']['random_mean']:.4f}, despite matched bins. Original common-neighbor mean is {result['comparison']['original_common_neighbor_mean']['hub']:.6f} versus {result['comparison']['original_common_neighbor_mean']['random_mean']:.6f}; original same-component fraction is {result['comparison']['original_same_component_fraction']['hub']:.4f} versus {result['comparison']['original_same_component_fraction']['random_mean']:.4f}. Thus the original-topology measures do not show a consistent general connectivity advantage.", '',
        f"After augmentation, alternative-path availability is {100 * result['comparison']['alternative_path_fraction']['hub']:.2f}% versus random mean {100 * result['comparison']['alternative_path_fraction']['random_mean']:.2f}%, and common-neighbor mean is {result['comparison']['augmented_common_neighbor_mean']['hub']:.4f} versus {result['comparison']['augmented_common_neighbor_mean']['random_mean']:.4f}. These alternative paths may use other synthetic edges; the measures can reflect collective synthetic-edge concentration and cycles. Hub augmentation leaves {result['comparison']['component_count']['hub']} components versus random mean {result['comparison']['component_count']['random_mean']:.1f}; more alternative paths therefore does not mean more global component merging.", '',
        'Hub endpoint degree is an explicit selection characteristic. The table tests whether it co-occurs with untyped local/path connectivity under the documented conditional baseline. Mixed, weak, or reversed effects must remain visible; selecting high-degree endpoints alone does not establish stronger relation-specific support. Untyped paths and common neighbors do not verify a directed relation or factual claim. No GNN, LLM training, KGQA experiment, attack-success evaluation or factual truth inference was performed. These diagnostics cannot establish that synthetic injections make KGQA harder.', '',
        'Reproduce: `python tools/analyze_structure_v2.py` from the project directory (or execute the script by absolute path). Standard library only; input paths and seed list can be overridden.']
    (args.report_dir / 'structural_support.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

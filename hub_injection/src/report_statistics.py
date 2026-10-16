"""Standard-library statistics and exportable SVG charts from actual data."""
import html
import math
from collections import Counter
from pathlib import Path
from .compute_degrees import compute_degrees
from .load_data import write_json


def describe(values):
    values = sorted(values)
    if not values:
        return {'count': 0, 'min': 0, 'max': 0, 'mean': 0, 'p50': 0, 'p90': 0, 'p99': 0}
    return {'count': len(values), 'min': values[0], 'max': values[-1],
            'mean': sum(values) / len(values),
            **{name: values[max(0, math.ceil(p * len(values)) - 1)]
               for name, p in [('p50', .5), ('p90', .9), ('p99', .99)]}}


def statistics(graph):
    degrees = compute_degrees(graph)
    return {
        'nodes': len(graph['nodes']), 'edges': len(graph['edges']),
        'relations': len(graph['relations']), 'qa_records': len(graph['questions']),
        'unresolved_paths': len(graph['unresolved_paths']),
        'entity_type_distribution': dict(sorted(Counter(n['entity_type'] for n in graph['nodes']).items())),
        'relation_distribution': dict(sorted(Counter(e['relation'] for e in graph['edges']).items())),
        'degree_distribution': {metric: describe([d[metric] for d in degrees.values()])
                                for metric in ('in_degree', 'out_degree', 'total_degree')},
        'total_degree_histogram': dict(sorted(Counter(d['total_degree'] for d in degrees.values()).items())),
        'isolated_nodes': sum(d['total_degree'] == 0 for d in degrees.values()),
        'self_loops': sum(e['source'] == e['target'] for e in graph['edges']),
        'edges_by_snapshot': dict(sorted(Counter(s for e in graph['edges'] for s in e['observed_in_snapshots']).items())),
        'edge_snapshot_combinations': dict(sorted(Counter('|'.join(e['observed_in_snapshots']) for e in graph['edges']).items())),
        'nodes_by_snapshot': dict(sorted(Counter(s for n in graph['nodes'] for s in n['observed_in_snapshots']).items())),
        'qa_by_snapshot': dict(sorted(Counter(q['snapshot'] for q in graph['questions']).items()))
    }


def injection_statistics(edges):
    return {
        'injected_edges': len(edges),
        'by_swap_entity_type': dict(sorted(Counter(e['injection_provenance']['entity_type'] for e in edges).items())),
        'by_relation': dict(sorted(Counter(e['relation'] for e in edges).items())),
        'by_snapshot_visibility': dict(sorted(Counter(s for e in edges for s in e['injection_snapshots']).items())),
        'by_snapshot_combination': dict(sorted(Counter('|'.join(e['injection_snapshots']) for e in edges).items())),
        'by_hub_pair': dict(sorted(Counter('|'.join(e['injection_provenance']['hub_pair']) for e in edges).items())),
        'by_changed_positions': dict(sorted(Counter('|'.join(s['position'] for s in e['injection_provenance']['swaps']) for e in edges).items())),
        'verified_false': 0, 'unverified': len(edges)
    }


def comparison_table(original, augmented, field):
    lines = ['| Category | Original | Augmented |', '|---|---:|---:|']
    for key in sorted(set(original[field]) | set(augmented[field])):
        lines.append(f'| {key} | {original[field].get(key, 0)} | {augmented[field].get(key, 0)} |')
    return '\n'.join(lines)


def bar_chart(path, title, counts):
    width, row, height = 920, 28, 100 + 28 * len(counts)
    scale = 540 / max(counts.values(), default=1)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',
           '<rect width="100%" height="100%" fill="white"/>',
           f'<text x="20" y="30" font-family="sans-serif" font-size="20">{html.escape(title)}</text>',
           '<text x="20" y="55" font-family="sans-serif" font-size="12">Synthetic injection counts; not verified factual falsity. Unique triples.</text>']
    for i, (label, count) in enumerate(sorted(counts.items())):
        y = 80 + i * row
        svg += [f'<text x="20" y="{y + 16}" font-family="sans-serif" font-size="13">{html.escape(label)}</text>',
                f'<rect x="260" y="{y}" width="{count * scale:.2f}" height="20" fill="#245c91"/>',
                f'<text x="{270 + count * scale:.2f}" y="{y + 16}" font-family="sans-serif" font-size="13">{count}</text>']
    svg.append('</svg>')
    Path(path).write_text('\n'.join(svg), encoding='utf-8')


def write_comparison(reports, original, augmented, injected, diagnostics):
    reports = Path(reports)
    stats = injection_statistics(injected)
    write_json(reports / 'augmented_statistics.json', augmented)
    write_json(reports / 'injection_statistics.json', {**stats, 'candidate_diagnostics': diagnostics})
    content = ['# Injection statistics', '', '| Metric | Original | Augmented |', '|---|---:|---:|']
    for key in ('nodes', 'edges', 'relations', 'qa_records', 'unresolved_paths', 'isolated_nodes', 'self_loops'):
        content.append(f'| {key} | {original[key]} | {augmented[key]} |')
    content += [f'| injected_edges | 0 | {len(injected)} |', '',
                'The budget is relative to original unique edges. Snapshot counts overlap because an edge can be visible in several snapshots.', '',
                '## Entity types', comparison_table(original, augmented, 'entity_type_distribution'), '',
                '## Relations', comparison_table(original, augmented, 'relation_distribution'), '',
                '## Edge snapshot visibility', comparison_table(original, augmented, 'edges_by_snapshot'), '',
                '## Original/augmented degrees (nearest-rank quantiles)', '```json']
    import json
    content += [json.dumps({'original': original['degree_distribution'], 'augmented': augmented['degree_distribution']}, indent=2), '```', '',
                '## Injection distributions', '```json', json.dumps(stats, indent=2), '```', '',
                '## Candidate decisions (final pool, first-failure counting)', '```json', json.dumps(diagnostics, indent=2), '```', '',
                'Relation-role compatibility uses positive original graph evidence; it is not a formal Wikidata ontology or factual verification. '
                'All original QA annotations were conservatively checked for identical positive triples; ambiguous multiple-intermediate second-hop pairings were not invented.']
    (reports / '03_injection_statistics.md').write_text('\n'.join(content) + '\n', encoding='utf-8')
    bar_chart(reports / 'injected_by_type.svg', 'Injected triples by swapped general entity type', stats['by_swap_entity_type'])
    bar_chart(reports / 'injected_by_relation.svg', 'Injected triples by relation', stats['by_relation'])

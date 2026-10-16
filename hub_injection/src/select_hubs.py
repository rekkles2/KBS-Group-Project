"""Rank using the ORIGINAL graph only; deterministic lexical QID ties."""
import math
from collections import defaultdict


def is_eligible(node):
    annotation = node.get('general_type_annotation', {})
    return (annotation.get('eligible_for_type_swap') is True
            and isinstance(node.get('entity_type'), str)
            and node['entity_type'].strip() not in {'', 'Unknown', 'unknown', 'Unresolved', 'Invalid'}
            and not annotation.get('data_quality_flags')
            and not node.get('data_quality_flags'))


def rank_eligible(graph, degrees):
    groups = defaultdict(list)
    for node in graph['nodes']:
        if is_eligible(node) and degrees[node['id']]['total_degree'] > 0:
            groups[node['entity_type']].append(node['id'])
    return {kind: sorted(ids, key=lambda q: (-degrees[q]['total_degree'], q))
            for kind, ids in sorted(groups.items())}


def initial_k(groups, top_k_max=20):
    if top_k_max < 2:
        raise ValueError('top-k-max must be at least 2')
    return {kind: min(len(ids), top_k_max, max(2, math.ceil(0.05 * len(ids))))
            if len(ids) >= 2 else 0 for kind, ids in groups.items()}


def expand_k(groups, sizes):
    """Deterministically double each selected prefix, up to complete eligibility."""
    return {kind: min(len(groups[kind]), max(k + 1, k * 2)) if k else 0
            for kind, k in sizes.items()}


def selected_hubs(groups, sizes):
    return {kind: ids[:sizes[kind]] for kind, ids in groups.items() if sizes[kind] >= 2}

"""Balanced deterministic sampling and explicitly synthetic provenance."""
import copy
import random
from collections import defaultdict, Counter
from decimal import Decimal, ROUND_HALF_EVEN
from .load_data import triple
from .snapshot_visibility import build_injection_visibility
from .factual_verification import annotate_factual_verification

SYNTHETIC_SEMANTICS = ('Synthetic overlay visibility inherited from a source QA-projection edge; '
                       'not QA support, historical truth, or a Wikidata validity interval.')


def injection_budget(original_unique_edges, ratio):
    ratio = Decimal(str(ratio))
    if not ratio.is_finite() or ratio < 0:
        raise ValueError('injection-ratio must be finite and nonnegative')
    return int((Decimal(original_unique_edges) * ratio).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))


def balanced_sample(candidates, count, seed):
    """Round-robin types, then relations within each type; seeded bucket order.

    Deduplication occurs before sampling. Uniform marginals are limited by
    available candidates; this is not sampling proportional to original edges.
    """
    rng = random.Random(seed)
    buckets = defaultdict(lambda: defaultdict(list))
    for candidate in candidates:
        buckets[candidate['entity_type']][candidate['relation']].append(candidate)
    types = sorted(buckets)
    rng.shuffle(types)
    relations, cursors = {}, Counter()
    for kind in types:
        relations[kind] = sorted(buckets[kind])
        rng.shuffle(relations[kind])
        for relation in relations[kind]:
            # Canonical caller-independent order before the seeded permutation.
            buckets[kind][relation].sort(key=triple)
            rng.shuffle(buckets[kind][relation])
    result = []
    while len(result) < count:
        progress = False
        for kind in types:
            available = relations[kind]
            for _ in range(len(available)):
                relation = available[cursors[kind] % len(available)]
                cursors[kind] += 1
                if buckets[kind][relation]:
                    result.append(buckets[kind][relation].pop())
                    progress = True
                    break
            if len(result) == count:
                break
        if not progress:
            break
    return sorted(result, key=triple)


def make_injected_edges(graph, chosen):
    result = []
    for candidate in chosen:
        original = graph['edges'][candidate['source_edge_index']]
        pair = candidate['hub_pair']
        swaps = [{'position': position, 'from': original[position], 'to': candidate[position]}
                 for position in ('source', 'target') if candidate[position] != original[position]]
        result.append({
            'source': candidate['source'], 'relation': candidate['relation'], 'target': candidate['target'],
            'value': 'fake',
            'observed_in_snapshots': list(original['observed_in_snapshots']), 'evidence': [],
            'edge_origin': 'synthetic_injection', 'is_poisoned': True,
            'injection_method': 'type_preserving_hub_swap',
            'injection_snapshots': list(original['observed_in_snapshots']),
            'source_observed_snapshots': list(original['observed_in_snapshots']),
            'snapshot_semantics': SYNTHETIC_SEMANTICS,
            'injection_provenance': {
                'source_edge_index': candidate['source_edge_index'],
                'original_source': original['source'], 'original_relation': original['relation'],
                'original_target': original['target'], 'hub_pair': pair,
                'pair_permutation': {pair[0]: pair[1], pair[1]: pair[0]},
                'entity_type': candidate['entity_type'], 'swaps': swaps,
                'source_observed_snapshots': list(original['observed_in_snapshots']),
                'source_question_ids': sorted({e['question_id'] for e in original['evidence']}),
                'source_evidence_references': copy.deepcopy(original['evidence']),
                'source_evidence_semantics': 'Source-edge derivation only; does not support the injected claim.',
                'compatibility_policy': 'original_directed_relation_role_and_counterpart_general_type',
                'original_qa_positive_evidence': 'no_identical_conservatively_projectable_triple',
                'factual_verification_status': 'unverified'
            }
        })
    annotate_factual_verification(graph, result)
    return result


def augment_graph(graph, injected, manifest):
    # Share read-only original objects; no caller function may mutate them.
    result = dict(graph)
    result['edges'] = list(graph['edges']) + injected
    result['metadata'] = dict(graph['metadata'])
    if 'task1_hub_injection' in result['metadata']:
        raise ValueError('Input already has Task 1 injection metadata')
    result['metadata']['task1_hub_injection'] = {
        'method': 'additive_type_preserving_pairwise_hub_swap',
        'release_schema_version': '2.0',
        'synthetic_class_semantics': 'value=fake labels synthetic edge construction, not independently verified factual falsity; no entity is marked fictitious.',
        'label_tables':{'edges':'edge_injection_labels.csv','nodes':'node_injection_labels.csv',
            'edge_target':'is_synthetic_edge: 1=injected, 0=original',
            'node_identity_target':'is_synthetic_node: all 0, no synthetic entity created',
            'node_participation_target':'incident_to_synthetic_edge: 1=endpoint of an injected relation, not a fake entity'},
        'source_statistics_semantics': 'metadata.stats is unchanged original-source statistics.',
        'snapshot_semantics': SYNTHETIC_SEMANTICS,
        'node_visibility_policy': 'Original node observation lists remain unchanged; overlay endpoints do not assert node QA occurrence.',
        'augmented_statistics': {'nodes': len(graph['nodes']), 'edges': len(result['edges']),
                                 'injected_edges': len(injected), 'qa_records': len(graph['questions'])},
        'configuration': manifest['configuration'], 'input_sha256': manifest['input_sha256'],
        'injection_visibility': build_injection_visibility(graph['nodes'], injected, graph['metadata']['snapshots']),
        'independently_verified_false_count': 0, 'unverified_synthetic_count': len(injected)
    }
    return result

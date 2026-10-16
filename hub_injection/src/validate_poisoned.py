"""Independent validation reconstructs transformations and directed evidence."""
from collections import defaultdict
from .load_data import triple
from .select_hubs import is_eligible
from .validate_original import qa_positive_triples
from .inject_misinformation import SYNTHETIC_SEMANTICS
from .snapshot_visibility import build_injection_visibility, snapshot_view
from .factual_verification import annotate_factual_verification


def validate_poisoned(original, poisoned, selected, target, require_target=True, evidence_cache_path=None):
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise ValueError(f'Poisoned validation failed: {name}')
    for key, value in original.items():
        if key not in {'edges', 'metadata'}:
            check(f'preserved_{key}', poisoned.get(key) == value)
    check('preserved_original_metadata', all(poisoned['metadata'].get(k) == v for k, v in original['metadata'].items()))
    length = len(original['edges'])
    check('preserved_original_edges_in_order', poisoned['edges'][:length] == original['edges'])
    injected = poisoned['edges'][length:]
    expected_truth=[dict(edge) for edge in injected]
    annotate_factual_verification(original,expected_truth,evidence_cache_path)
    check('factual_verdicts_match_explicit_evidence_context',all(
        edge['factual_verification']==expected['factual_verification'] for edge,expected in zip(injected,expected_truth)))
    check('exact_budget_or_documented_shortfall', len(injected) == target if require_target else len(injected) <= target)
    check('unique_augmented_triples', len({triple(e) for e in poisoned['edges']}) == len(poisoned['edges']))
    namespace = poisoned['metadata']['task1_hub_injection']
    check('accurate_namespaced_augmented_statistics', namespace['augmented_statistics'] == {
        'nodes':len(original['nodes']), 'edges':len(poisoned['edges']),
        'injected_edges':len(injected), 'qa_records':len(original['questions'])})
    check('accurate_namespaced_verification_counts', namespace['independently_verified_false_count'] == 0
          and namespace['unverified_synthetic_count'] == len(injected))
    nodes = {n['id']: n for n in original['nodes']}
    check('exact_overlay_visibility', namespace['injection_visibility'] == build_injection_visibility(
        original['nodes'],injected,original['metadata']['snapshots']))
    for snapshot in original['metadata']['snapshots']:
        view=snapshot_view(poisoned,snapshot)
        visible={node['record']['id'] for node in view['nodes']}
        check('all_snapshot_endpoints_renderable',all(e['record']['source'] in visible and e['record']['target'] in visible for e in view['edges']))
    relations = {r['id'] for r in original['relations']}
    positives = qa_positive_triples(original)
    original_triples = {triple(e) for e in original['edges']}
    # These signatures are reconstructed here independently of the worker.
    incoming, outgoing = defaultdict(set), defaultdict(set)
    for edge in original['edges']:
        outgoing[edge['source']].add((edge['relation'], nodes[edge['target']]['entity_type']))
        incoming[edge['target']].add((edge['relation'], nodes[edge['source']]['entity_type']))
    for edge in injected:
        check('injected_references_resolve', edge['source'] in nodes and edge['target'] in nodes and edge['relation'] in relations)
        check('no_injected_self_loops', edge['source'] != edge['target'])
        check('no_qa_positive_triples', triple(edge) not in positives)
        check('no_original_triples', triple(edge) not in original_triples)
        check('explicit_synthetic_identity', edge['edge_origin'] == 'synthetic_injection'
              and edge['is_poisoned'] is True and edge['injection_method'] == 'type_preserving_hub_swap'
              and edge['value'] == 'fake')
        provenance = edge['injection_provenance']
        index = provenance['source_edge_index']
        check('valid_source_edge_index', isinstance(index, int) and 0 <= index < length)
        source = original['edges'][index]
        check('exact_source_triple', (provenance['original_source'], provenance['original_relation'], provenance['original_target']) == triple(source))
        a, b = provenance['hub_pair']
        check('eligible_same_type_hubs', a != b and a in nodes and b in nodes
              and is_eligible(nodes[a]) and is_eligible(nodes[b])
              and nodes[a]['entity_type'] == nodes[b]['entity_type'] == provenance['entity_type'])
        check('selected_hubs_only', a in selected[provenance['entity_type']] and b in selected[provenance['entity_type']])
        permutation = {a: b, b: a}
        expected = (permutation.get(source['source'], source['source']), source['relation'],
                    permutation.get(source['target'], source['target']))
        check('pairwise_permutation_both_endpoints', triple(edge) == expected and triple(edge) != triple(source)
              and provenance['pair_permutation'] == permutation)
        swaps = [{'position': p, 'from': source[p], 'to': edge[p]}
                 for p in ('source', 'target') if source[p] != edge[p]]
        check('complete_swap_provenance', provenance['swaps'] == swaps)
        for swap in swaps:
            position, donor = swap['position'], swap['to']
            role_evidence = outgoing[donor] if position == 'source' else incoming[donor]
            counterpart = edge['target'] if position == 'source' else edge['source']
            check('directed_role_compatibility', (edge['relation'], nodes[counterpart]['entity_type']) in role_evidence)
        snaps = source['observed_in_snapshots']
        check('source_overlay_snapshot_identity', edge['observed_in_snapshots'] == edge['injection_snapshots']
              == edge['source_observed_snapshots'] == provenance['source_observed_snapshots'] == snaps)
        check('synthetic_snapshot_semantics', edge['snapshot_semantics'] == SYNTHETIC_SEMANTICS)
        check('qa_evidence_not_synthetic_support', edge['evidence'] == []
              and provenance['source_question_ids'] == sorted({e['question_id'] for e in source['evidence']})
              and provenance['source_evidence_references'] == source['evidence'])
        check('honest_factual_status', provenance['factual_verification_status'] == 'unverified')
        factual=edge['factual_verification']
        check('separate_factual_verification', factual['status'] in {'unresolved','verified_true','verified_false'}
              and bool(factual['method']) and bool(factual['reason'])
              and (factual['status']=='unresolved' or bool(factual['evidence_refs'])))
        # Exact allowed fields exclude accidental historical validity qualifiers.
        check('no_added_validity_fields', set(edge) == {
            'source','relation','target','observed_in_snapshots','evidence','edge_origin','is_poisoned',
            'injection_method','injection_snapshots','source_observed_snapshots','snapshot_semantics','injection_provenance',
            'value','factual_verification'})
    return {'passed': all(checks.values()), 'checks': checks, 'injected_count': len(injected),
            'total_edges': len(poisoned['edges'])}

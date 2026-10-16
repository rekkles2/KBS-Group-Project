"""Pairwise candidate enumeration contributed by OpenCode kimi-k2.6.

Raw response: reports/reviews/implementation_retry_response.json. Coordinator
adapted attribute access to actual JSON dictionaries, reused strict eligibility,
added duplicate/isolated-hub guards and validated original edge references.
"""
import itertools
from collections import defaultdict
from .select_hubs import is_eligible


def generate_candidates(graph, hubs, forbidden_triples=None):
    node_map = {n['id']: n for n in graph['nodes']}
    edges = graph['edges']
    relations = {r['id'] for r in graph['relations']}
    validated = {}
    for kind, qids in hubs.items():
        if len(set(qids)) != len(qids):
            raise ValueError(f'Duplicate hub identifiers for {kind}')
        for qid in qids:
            if qid not in node_map:
                raise ValueError(f'Hub {qid} missing')
            node = node_map[qid]
            if node['entity_type'] != kind or not is_eligible(node):
                raise ValueError(f'Hub {qid} has mismatched type, flags or ineligibility')
        validated[kind] = list(qids)

    incidence = defaultdict(set)
    out_evidence, in_evidence = defaultdict(set), defaultdict(set)
    original_triples = set()
    for index, edge in enumerate(edges):
        source, relation, target = edge['source'], edge['relation'], edge['target']
        if source not in node_map or target not in node_map or relation not in relations:
            raise ValueError(f'Invalid original edge reference at index {index}')
        incidence[source].add(index)
        incidence[target].add(index)
        source_type, target_type = node_map[source]['entity_type'], node_map[target]['entity_type']
        out_evidence[source].add((relation, target_type))
        in_evidence[target].add((relation, source_type))
        original_triples.add((source, relation, target))
    for qids in validated.values():
        for qid in qids:
            if not incidence[qid]:
                raise ValueError(f'Isolated hub {qid}')

    forbidden_set = set(forbidden_triples or ())
    candidates, seen, rejected, attempted = [], set(), defaultdict(int), 0
    for kind in sorted(validated):
        for a, b in itertools.combinations(sorted(validated[kind]), 2):
            for edge_index in sorted(incidence[a] | incidence[b]):
                attempted += 1
                edge = edges[edge_index]
                old_source, relation, old_target = edge['source'], edge['relation'], edge['target']
                source = b if old_source == a else (a if old_source == b else old_source)
                target = b if old_target == a else (a if old_target == b else old_target)
                changed = [position for position, old, new in
                           [('source',old_source,source),('target',old_target,target)] if old != new]
                proposed = source, relation, target
                reason = None
                if source == target:
                    reason = 'self_loop'
                elif source not in node_map or target not in node_map:
                    reason = 'invalid_endpoint'
                elif 'source' in changed and (relation,node_map[target]['entity_type']) not in out_evidence[source]:
                    reason = 'missing_source_donor_evidence'
                elif 'target' in changed and (relation,node_map[source]['entity_type']) not in in_evidence[target]:
                    reason = 'missing_target_donor_evidence'
                elif proposed in original_triples:
                    reason = 'original_triple'
                elif proposed in forbidden_set:
                    reason = 'forbidden_triple'
                elif proposed in seen:
                    reason = 'duplicate'
                if reason:
                    rejected[reason] += 1
                    continue
                seen.add(proposed)
                candidates.append({'source':source, 'relation':relation, 'target':target,
                    'source_edge_index':edge_index, 'hub_pair':[a,b], 'entity_type':kind,
                    'changed_positions':changed})
    candidates.sort(key=lambda c:(c['source'],c['relation'],c['target'],c['hub_pair'][0],c['hub_pair'][1]))
    return candidates, {'attempted':attempted, 'accepted_unique':len(candidates),
                        'rejected_by_reason':dict(sorted(rejected.items()))}

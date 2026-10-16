"""Input integrity and conservative positive-evidence checks over all QA."""
import re
from collections import Counter
from .load_data import triple

QID = re.compile(r'^Q[1-9][0-9]*$')
PID = re.compile(r'^P[1-9][0-9]*$')
EXPECTED = {'nodes': 7868, 'edges': 7737, 'relations': 20, 'questions': 18436, 'unresolved_paths': 496}


def qa_positive_triples(graph):
    """No Cartesian second-hop pairing when more than one intermediate exists.

    Include valid first hops even in excluded QA; include second hops only for
    exactly one intermediate. These are positive annotation evidence, not a
    complete set of historical Wikidata facts.
    """
    positives = set()
    for question in graph['questions']:
        record = question['source_record']
        subject = record.get('subject', {}).get('subject')
        rels = record.get('relations', [])
        answers = [x.get('ID') for x in record.get('answer annotations', [])]
        # Duplicate annotations of the same QID do not create pairing ambiguity.
        mids = list(dict.fromkeys(x.get('ID') for x in record.get('intermediate entities', [])))
        proposed = []
        if len(rels) == 1:
            proposed.extend((subject, rels[0], answer) for answer in answers)
        elif len(rels) == 2:
            proposed.extend((subject, rels[0], mid) for mid in mids)
            if len(mids) == 1:
                proposed.extend((mids[0], rels[1], answer) for answer in answers)
        for s, r, t in proposed:
            if (isinstance(s, str) and QID.fullmatch(s) and isinstance(t, str)
                    and QID.fullmatch(t) and isinstance(r, str) and PID.fullmatch(r)):
                positives.add((s, r, t))
    return positives


def validate_original(graph, rows):
    for key in ('metadata', 'nodes', 'relations', 'edges', 'questions', 'unresolved_paths'):
        if key not in graph:
            raise ValueError(f'Missing top-level field: {key}')
    nodes = {n['id']: n for n in graph['nodes']}
    relations = {r['id'] for r in graph['relations']}
    questions = {q['id']: q for q in graph['questions']}
    snapshots = set(graph['metadata']['snapshots'])
    csv_rows = {r['wikidata_id']: r for r in rows}
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise ValueError(f'Original integrity check failed: {name}')
    check('unique_qids', len(nodes) == len(graph['nodes']))
    check('valid_qids', all(QID.fullmatch(q) for q in nodes))
    check('unique_relations', len(relations) == len(graph['relations']))
    check('valid_relations', all(PID.fullmatch(r) for r in relations))
    check('unique_qa_ids', len(questions) == len(graph['questions']))
    check('unique_original_triples', len({triple(e) for e in graph['edges']}) == len(graph['edges']))
    check('csv_unique_qids', len(csv_rows) == len(rows))
    check('csv_node_coverage', csv_rows.keys() == nodes.keys())
    check('known_snapshot_ids', snapshots == {'Dec2021', 'Dec2023', 'March2024'})
    for node in graph['nodes']:
        row = csv_rows[node['id']]
        ann = node['general_type_annotation']
        check_node = (row['entity_type'] == node['entity_type']
                      and row['eligible_for_type_swap'] == str(ann['eligible_for_type_swap'])
                      and set(filter(None, row['data_quality_flags'].split('|'))) == set(ann['data_quality_flags'])
                      and row['type_policy_version'] == ann['policy_version']
                      and set(filter(None, row['detailed_type_ids'].split('|'))) == {d['id'] for d in node['detailed_entity_types']}
                      and isinstance(ann['eligible_for_type_swap'], bool)
                      and isinstance(ann['data_quality_flags'], list)
                      and isinstance(node['entity_type'], str)
                      and set(node['observed_in_snapshots']) <= snapshots)
        if not check_node:
            raise ValueError(f'Node/CSV disagreement: {node["id"]}')
    checks['all_node_csv_types_eligibility_flags_consistent'] = True
    for edge in graph['edges']:
        if not (edge['source'] in nodes and edge['target'] in nodes and edge['relation'] in relations):
            raise ValueError(f'Dangling original edge: {triple(edge)}')
        if not set(edge['observed_in_snapshots']) <= snapshots:
            raise ValueError('Invalid edge snapshot')
        evidence_snapshots = set()
        for evidence in edge['evidence']:
            if evidence['question_id'] not in questions or evidence['hop'] not in (1, 2):
                raise ValueError('Invalid evidence reference')
            question = questions[evidence['question_id']]
            evidence_snapshots.add(question['snapshot'])
            if (triple(edge) not in qa_positive_triples({'questions': [question]})
                    or question['source_record']['relations'][evidence['hop'] - 1] != edge['relation']):
                raise ValueError('Evidence does not project to cited edge')
        if evidence_snapshots != set(edge['observed_in_snapshots']):
            raise ValueError('Original snapshot/evidence mismatch')
        for endpoint in (edge['source'], edge['target']):
            if not set(edge['observed_in_snapshots']) <= set(nodes[endpoint]['observed_in_snapshots']):
                raise ValueError('Original edge visibility missing from endpoint observations')
    checks['original_endpoints_relations_evidence_snapshots_valid'] = True
    check('qa_snapshot_ids', all(q['snapshot'] in snapshots for q in graph['questions']))
    check('unresolved_qa_references', all(u['question_id'] in questions and u['snapshot'] in snapshots
                                         for u in graph['unresolved_paths']))
    for key in ('snapshot_semantics', 'node_snapshot_semantics', 'projection_semantics', 'pairing_policy'):
        check(f'metadata_{key}', bool(graph['metadata'].get(key)))
    counts = {key: len(graph[key]) for key in EXPECTED}
    return {'checks': checks, 'counts': counts, 'expected_counts': EXPECTED,
            'discrepancies': {k: {'expected': EXPECTED[k], 'actual': v} for k, v in counts.items() if v != EXPECTED[k]},
            'qa_positive_triples': len(qa_positive_triples(graph)),
            'flag_counts': dict(Counter(flag for n in graph['nodes'] for flag in n['general_type_annotation']['data_quality_flags'])),
            'qa_records_with_duplicate_intermediate_qids': sum(
                len(q['source_record'].get('intermediate entities', [])) !=
                len({x.get('ID') for x in q['source_record'].get('intermediate entities', [])})
                for q in graph['questions'])}

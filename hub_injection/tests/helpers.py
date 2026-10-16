def node(qid, kind, eligible=True, flags=None):
    return {'id': qid, 'entity_type': kind, 'labels': [qid], 'observed_in_snapshots': ['Dec2021'],
            'general_type_annotation': {'eligible_for_type_swap': eligible, 'data_quality_flags': flags or []}}


def edge(source, relation, target, snapshots=None):
    return {'source': source, 'relation': relation, 'target': target,
            'observed_in_snapshots': ['Dec2021'] if snapshots is None else snapshots, 'evidence': []}


def fixture():
    return {'metadata': {'snapshots': ['Dec2021', 'Dec2023', 'March2024'], 'snapshot_semantics': 'annotation observations'},
            'nodes': [node(q, 'Person') for q in ['Q1', 'Q2', 'Q3']] + [node(q, 'SportsTeam') for q in ['Q10', 'Q11']],
            'relations': [{'id': p} for p in ['P54', 'P286', 'P26']],
            'edges': [edge('Q1','P54','Q10'), edge('Q2','P54','Q11'), edge('Q10','P286','Q1'),
                      edge('Q11','P286','Q2'), edge('Q1','P26','Q2'), edge('Q2','P26','Q3'), edge('Q3','P26','Q1')],
            'questions': [], 'unresolved_paths': []}

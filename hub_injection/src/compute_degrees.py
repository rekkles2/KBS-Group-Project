"""Count directed multirelational edges; each self-loop contributes two total."""


def compute_degrees(graph):
    degrees = {n['id']: {'in_degree': 0, 'out_degree': 0, 'total_degree': 0}
               for n in graph['nodes']}
    for edge in graph['edges']:
        degrees[edge['source']]['out_degree'] += 1
        degrees[edge['target']]['in_degree'] += 1
    for values in degrees.values():
        values['total_degree'] = values['in_degree'] + values['out_degree']
    return degrees

"""Non-mutating adapter distinguishing QA-observed and overlay-visible nodes."""


def build_injection_visibility(nodes, injected, snapshots):
    node_map={n['id']:n for n in nodes}
    result={}
    for snapshot in snapshots:
        activated=set()
        count=0
        for edge in injected:
            if snapshot not in edge['injection_snapshots']:
                continue
            count+=1
            for position in ('source','target'):
                qid=edge[position]
                if qid not in node_map:
                    raise ValueError(f'Unknown overlay endpoint: {qid}')
                if snapshot not in node_map[qid]['observed_in_snapshots']:
                    activated.add(qid)
        result[snapshot]={'synthetically_visible_nodes':sorted(activated),
                          'reason':'synthetic_edge_endpoint', 'injected_visible_edges':count}
    return result


def snapshot_view(graph, snapshot):
    """Return copied view wrappers, keeping original nodes/edges untouched.

    A synthetic edge is identified by edge_origin, not factual-verification status
    or the class-label word 'fake'. A real node never becomes a fictitious entity.
    """
    snapshots=graph['metadata']['snapshots']
    if snapshot not in snapshots:raise ValueError(f'Unknown snapshot: {snapshot}')
    namespace=graph['metadata'].get('task1_hub_injection',{})
    overlay=namespace.get('injection_visibility',{}).get(snapshot,{}).get('synthetically_visible_nodes',[])
    observed={n['id'] for n in graph['nodes'] if snapshot in n['observed_in_snapshots']}
    activated=set(overlay)
    node_map={n['id']:n for n in graph['nodes']}
    if not activated<=node_map.keys():raise ValueError('Unknown synthetically visible node')
    visible=observed|activated
    edge_views=[]
    for edge in graph['edges']:
        synthetic=edge.get('edge_origin')=='synthetic_injection'
        field='injection_snapshots' if synthetic else 'observed_in_snapshots'
        if snapshot in edge[field]:
            if edge['source'] not in visible or edge['target'] not in visible:
                raise ValueError('Snapshot edge endpoint is not renderable')
            edge_views.append({'record':edge,'synthetic':synthetic,
                               'style_class':'synthetic-edge' if synthetic else 'observed-edge'})
    return {'snapshot':snapshot,
            'nodes':[{'record':node_map[qid], 'originally_observed':qid in observed,
                      'synthetically_activated':qid in activated,
                      'style_class':'overlay-activated-node' if qid in activated else 'observed-node'}
                     for qid in sorted(visible)],
            'edges':edge_views,
            'legend':{'synthetic-edge':'Synthetic class fake; not verified factual falsity.',
                      'overlay-activated-node':'Real entity made renderable by synthetic overlay, not an original QA observation.'}}

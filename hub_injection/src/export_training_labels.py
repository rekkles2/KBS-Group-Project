"""Explicit construction labels, distinct from adjudicated factual truth."""
from collections import Counter
import csv
from pathlib import Path


def write_training_labels(original, augmented, outputs):
    outputs=Path(outputs);outputs.mkdir(parents=True,exist_ok=True)
    original_nodes={n['id'] for n in original['nodes']}
    incoming,outgoing=Counter(),Counter()
    edge_fields=['edge_index','source','relation','target','is_synthetic_edge','synthetic_class','factual_verification_status']
    synthetic_count=0
    with (outputs/'edge_injection_labels.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=edge_fields);writer.writeheader()
        for index,edge in enumerate(augmented['edges']):
            synthetic=edge.get('edge_origin')=='synthetic_injection'
            if synthetic:
                synthetic_count+=1;outgoing[edge['source']]+=1;incoming[edge['target']]+=1
            writer.writerow({'edge_index':index,'source':edge['source'],'relation':edge['relation'],'target':edge['target'],
                'is_synthetic_edge':int(synthetic),'synthetic_class':'fake' if synthetic else 'original',
                'factual_verification_status':edge['factual_verification']['status'] if synthetic else 'not_adjudicated'})
    node_fields=['qid','entity_type','is_synthetic_node','incident_to_synthetic_edge','synthetic_in_degree','synthetic_out_degree','synthetic_total_degree']
    incident=0
    with (outputs/'node_injection_labels.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=node_fields);writer.writeheader()
        for node in sorted(augmented['nodes'],key=lambda n:n['id']):
            qid=node['id'];total=incoming[qid]+outgoing[qid];incident+=int(total>0)
            writer.writerow({'qid':qid,'entity_type':node['entity_type'],'is_synthetic_node':int(qid not in original_nodes),
                'incident_to_synthetic_edge':int(total>0),'synthetic_in_degree':incoming[qid],
                'synthetic_out_degree':outgoing[qid],'synthetic_total_degree':total})
    return {'edge_rows':len(augmented['edges']),'synthetic_edges':synthetic_count,'node_rows':len(augmented['nodes']),
            'synthetic_nodes':len({n['id'] for n in augmented['nodes']}-original_nodes),'nodes_incident_to_synthetic_edges':incident,
            'semantics':'Construction labels only. Node incidence means participation in synthetic relations, not fictitious entity or verified false fact.'}

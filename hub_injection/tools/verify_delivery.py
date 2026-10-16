#!/usr/bin/env python3
"""Check the actual delivered files, without regenerating or changing inputs."""
import ast
import csv
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.load_data import sha256,write_json


def main():
    manifest=json.loads((ROOT/'outputs/injection_manifest.json').read_text(encoding='utf-8'))
    original=json.loads((ROOT.parents[1]/'pat_kg_merged.json').read_text(encoding='utf-8-sig'))
    augmented=json.loads((ROOT/'outputs/pat_kg_poisoned_10pct.json').read_text(encoding='utf-8'))
    injected=[json.loads(line) for line in (ROOT/'outputs/injected_edges.jsonl').read_text(encoding='utf-8').splitlines()]
    checks={}
    def check(name,value):
        checks[name]=bool(value)
        if not value:raise ValueError(f'Delivery verification failed: {name}')
    for name,expected in manifest['output_sha256'].items():
        check('output_hash_'+name,sha256(ROOT/'outputs'/name)==expected)
    for name,expected in manifest['source_code_sha256'].items():
        check('source_hash_'+name,sha256(ROOT/name)==expected)
    check('original_graph_hash',sha256(ROOT.parents[1]/'pat_kg_merged.json')==manifest['input_sha256']['graph'])
    check('original_csv_hash',sha256(ROOT.parents[1]/'entity_id_value_type.csv')==manifest['input_sha256']['entity_csv'])
    check('jsonl_equals_appended_graph_edges',injected==augmented['edges'][len(original['edges']):])
    check('jsonl_count_matches_manifest',len(injected)==manifest['actual_injected_edges']==774)
    check('total_edges_8511',len(augmented['edges'])==8511)
    check('original_nodes_qa_relations_unresolved_equal',all(original[k]==augmented[k] for k in ['nodes','questions','relations','unresolved_paths']))
    check('original_edge_prefix_equal',original['edges']==augmented['edges'][:len(original['edges'])])
    check('original_metadata_equal',all(augmented['metadata'][k]==v for k,v in original['metadata'].items()))
    entry=ROOT.parent/'pat_kg_poisoned_10pct.json'
    check('top_level_graph_exists_and_matches',sha256(entry)==manifest['output_sha256']['pat_kg_poisoned_10pct.json'])
    # A normal copied file or an archive extraction is supported; no hardlink prerequisite.
    with (ROOT/'outputs/hub_nodes.csv').open(encoding='utf-8',newline='') as stream:rows=list(csv.DictReader(stream))
    check('selected_hub_csv_count',sum(r['selected_top_k']=='True' for r in rows)==sum(manifest['k_by_type'].values())==206)
    for chart in ['injected_by_type.svg','injected_by_relation.svg']:
        ET.parse(ROOT/'reports'/chart)
    checks['svg_charts_parse']=True
    for path in ROOT.rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    checks['all_delivered_python_syntax_valid']=True
    reviews_path=ROOT/'reports/multi_model_review/summary.json'
    if reviews_path.exists():
        reviews=json.loads(reviews_path.read_text(encoding='utf-8'))
        check('multi_model_consensus',reviews['consensus'] is True)
    tests=json.loads((ROOT/'reports/tests_summary.json').read_text(encoding='utf-8'))
    check('all_tests_passed_no_skip',tests['successful'] and tests['passed']==tests['tests_run'] and tests['skipped']==0)
    added=augmented['edges'][len(original['edges']):]
    check('all_774_edges_value_fake',sum(e.get('value')=='fake' for e in added)==774)
    with (ROOT/'outputs/edge_injection_labels.csv').open(encoding='utf-8',newline='') as stream:
        edge_labels=list(csv.DictReader(stream))
    check('all_edge_training_labels_align_with_records',len(edge_labels)==len(augmented['edges']) and all(
        int(row['edge_index'])==i and (row['source'],row['relation'],row['target'])==(edge['source'],edge['relation'],edge['target'])
        and int(row['is_synthetic_edge'])==int(i>=len(original['edges'])) for i,(row,edge) in enumerate(zip(edge_labels,augmented['edges']))))
    from collections import Counter
    indegree=Counter(e['target'] for e in added);outdegree=Counter(e['source'] for e in added)
    with (ROOT/'outputs/node_injection_labels.csv').open(encoding='utf-8',newline='') as stream:
        node_labels=list(csv.DictReader(stream))
    check('all_node_training_labels_align_with_injected_endpoints',len(node_labels)==len(original['nodes']) and
          {r['qid'] for r in node_labels}=={n['id'] for n in original['nodes']} and all(
          r['is_synthetic_node']=='0' and int(r['incident_to_synthetic_edge'])==int(indegree[r['qid']]+outdegree[r['qid']]>0)
          and int(r['synthetic_in_degree'])==indegree[r['qid']] and int(r['synthetic_out_degree'])==outdegree[r['qid']]
          and int(r['synthetic_total_degree'])==indegree[r['qid']]+outdegree[r['qid']] for r in node_labels))
    check('no_real_node_marked_fake',not any(n.get('value')=='fake' for n in augmented['nodes']))
    check('factual_class_separate_from_truth',all(e['factual_verification']['status']=='unresolved' and e['injection_provenance']['factual_verification_status']=='unverified' for e in added))
    from src.snapshot_visibility import snapshot_view
    for snapshot in original['metadata']['snapshots']:
        view=snapshot_view(augmented,snapshot)
        visible={n['record']['id'] for n in view['nodes']}
        check('renderable_'+snapshot,all(e['record']['source'] in visible and e['record']['target'] in visible for e in view['edges']))
    # Exact credential scan; never report key contents or include them in output.
    key_path=Path('E:/DevSpaceProjects/.opencode-local/api_key.txt')
    if key_path.exists():
        secret=key_path.read_text(encoding='utf-8-sig').strip().encode('utf-8')
        leaks=[str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
               and secret and secret in p.read_bytes()]
        check('no_copied_api_credential',not leaks)
    write_json(ROOT/'reports/final_verification.json',{'passed':all(checks.values()),'checks':checks,
        'graph_entry':str(entry),'graph_sha256':sha256(entry),'unit_integration_tests':tests,
        'source_inputs_unchanged':True,'delivered_graph_bytes':entry.stat().st_size})
    print(json.dumps({'passed':True,'file_checks':len(checks),'graph_sha256':sha256(entry),
                      'graph_bytes':entry.stat().st_size,'tests':tests['passed']},indent=2))


if __name__=='__main__':
    main()

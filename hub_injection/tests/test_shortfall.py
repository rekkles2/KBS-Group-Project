"""Analytical fixture for prefix expansion and a precisely impossible budget."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from run_task1 import run
from tests.helpers import node, edge


class ShortfallTests(unittest.TestCase):
    def test_full_expansion_reports_maximum_without_fabricating_edges(self):
        with tempfile.TemporaryDirectory(prefix='pat-shortfall-') as temporary:
            root=Path(temporary)
            nodes=[node(q,'Person') for q in ['Q1','Q2','Q3']]
            for n in nodes:
                n['detailed_entity_types']=[]
                n['general_type_annotation']['policy_version']='2.1'
            graph={'metadata':{'snapshots':['Dec2021','Dec2023','March2024'],
                'snapshot_semantics':'QA observations', 'node_snapshot_semantics':'QA occurrence',
                'projection_semantics':'QA projection', 'pairing_policy':'no ambiguous second-hop pairs'},
                'nodes':nodes, 'relations':[{'id':'P26'}],
                'edges':[edge('Q1','P26','Q2',[]),edge('Q2','P26','Q3',[]),edge('Q3','P26','Q1',[])],
                'questions':[], 'unresolved_paths':[]}
            graph_path=root/'original.json'; graph_path.write_text(json.dumps(graph),encoding='utf-8')
            csv_path=root/'entities.csv'
            with csv_path.open('w',encoding='utf-8',newline='') as stream:
                fields=['wikidata_id','entity_type','eligible_for_type_swap','data_quality_flags','type_policy_version','detailed_type_ids']
                writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
                for n in nodes:
                    writer.writerow({'wikidata_id':n['id'],'entity_type':'Person','eligible_for_type_swap':'True',
                                     'data_quality_flags':'','type_policy_version':'2.1','detailed_type_ids':''})
            result=run(graph_path,csv_path,root/'run',ratio='10',seed=42)
            # Three directed non-self reverse-cycle edges are the complete complement.
            self.assertEqual(result['status'],'PARTIAL')
            self.assertEqual(result['injected_edges'],3)
            self.assertEqual(result['expansion_rounds'],1)
            manifest=json.loads((root/'run/outputs/injection_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['target_injected_edges'],30)
            self.assertEqual(manifest['candidate_count'],3)
            self.assertEqual(manifest['k_by_type'],{'Person':3})
            self.assertIsNotNone(manifest['shortfall_reason'])
            self.assertEqual(graph,json.loads(graph_path.read_text(encoding='utf-8')))

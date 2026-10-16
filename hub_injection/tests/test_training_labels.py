import csv
import tempfile
from pathlib import Path
import unittest
from src.export_training_labels import write_training_labels
from src.generate_candidates import generate_candidates
from src.inject_misinformation import make_injected_edges,augment_graph
from tests.helpers import fixture


class TrainingLabelTests(unittest.TestCase):
    def test_node_incidence_separate_from_fictitious_node_and_edge_truth(self):
        original=fixture();c=generate_candidates(original,{'Person':['Q1','Q2']})[0][:1]
        injected=make_injected_edges(original,c);graph=augment_graph(original,injected,{'configuration':{},'input_sha256':{}})
        with tempfile.TemporaryDirectory() as tmp:
            stats=write_training_labels(original,graph,tmp)
            nodes=list(csv.DictReader((Path(tmp)/'node_injection_labels.csv').open(encoding='utf-8')))
            edges=list(csv.DictReader((Path(tmp)/'edge_injection_labels.csv').open(encoding='utf-8')))
        self.assertEqual(stats['synthetic_nodes'],0)
        self.assertTrue(all(n['is_synthetic_node']=='0' for n in nodes))
        self.assertEqual(sum(n['incident_to_synthetic_edge']=='1' for n in nodes),2)
        self.assertEqual(sum(int(n['synthetic_total_degree']) for n in nodes),2)
        self.assertEqual(sum(e['is_synthetic_edge']=='1' for e in edges),1)
        self.assertTrue(all(e['synthetic_class']=='original' and e['factual_verification_status']=='not_adjudicated' for e in edges[:-1]))
        self.assertEqual(edges[-1]['factual_verification_status'],'unresolved')

    def test_empty_overlay_all_original_labels(self):
        original=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            stats=write_training_labels(original,original,tmp)
        self.assertEqual(stats['synthetic_edges'],0)
        self.assertEqual(stats['nodes_incident_to_synthetic_edges'],0)

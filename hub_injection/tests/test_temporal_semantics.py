import copy
import unittest
from src.generate_candidates import generate_candidates
from src.inject_misinformation import make_injected_edges, augment_graph, SYNTHETIC_SEMANTICS
from src.validate_poisoned import validate_poisoned
from tests.helpers import fixture


class TemporalTests(unittest.TestCase):
    def setUp(self):
        self.graph = fixture()
        self.hubs = {'Person':['Q1','Q2']}
        self.candidate = next(c for c in generate_candidates(self.graph, self.hubs)[0]
                              if c['relation']=='P54' and c['source']=='Q2')

    def test_source_snapshots_and_qa_derivation_only(self):
        source = self.graph['edges'][self.candidate['source_edge_index']]
        source['observed_in_snapshots'] = ['Dec2021','March2024']
        source['evidence'] = [{'question_id':'source-question', 'hop':1}]
        synthetic = make_injected_edges(self.graph, [self.candidate])[0]
        self.assertEqual(synthetic['injection_snapshots'], ['Dec2021','March2024'])
        self.assertEqual(synthetic['evidence'], [])
        self.assertEqual(synthetic['injection_provenance']['source_question_ids'], ['source-question'])
        self.assertEqual(synthetic['snapshot_semantics'], SYNTHETIC_SEMANTICS)
        self.assertEqual(synthetic['injection_provenance']['factual_verification_status'], 'unverified')

    def test_original_objects_and_metadata_untouched(self):
        before = copy.deepcopy(self.graph)
        injected = make_injected_edges(self.graph, [self.candidate])
        poisoned = augment_graph(self.graph, injected, {'configuration':{},'input_sha256':{}})
        self.assertEqual(self.graph, before)
        self.assertEqual(poisoned['nodes'], before['nodes'])
        self.assertEqual(poisoned['edges'][:-1], before['edges'])
        self.assertEqual(poisoned['metadata']['snapshot_semantics'], before['metadata']['snapshot_semantics'])

    def test_validation_rejects_false_qa_support_and_invented_validity(self):
        injected = make_injected_edges(self.graph, [self.candidate])
        poisoned = augment_graph(self.graph, injected, {'configuration':{},'input_sha256':{}})
        for field, value in [('evidence',[{'question_id':'fake','hop':1}]), ('valid_from','2021-01-01'),
                             ('observed_in_snapshots',['Dec2023'])]:
            broken = copy.deepcopy(poisoned)
            broken['edges'][-1][field] = value
            with self.assertRaises(ValueError): validate_poisoned(self.graph, broken, self.hubs, 1)

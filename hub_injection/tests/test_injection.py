import copy
import unittest
from src.generate_candidates import generate_candidates
from src.inject_misinformation import injection_budget, balanced_sample, make_injected_edges, augment_graph
from src.validate_poisoned import validate_poisoned
from src.validate_original import qa_positive_triples
from tests.helpers import fixture


class InjectionTests(unittest.TestCase):
    def setUp(self):
        self.graph = fixture()
        self.hubs = {'Person':['Q1','Q2']}

    def test_budget_exact_decimal_half_even(self):
        self.assertEqual(injection_budget(7737, '.10'), 774)
        self.assertEqual(injection_budget(5, '.5'), 2)
        self.assertEqual(injection_budget(7, '.5'), 4)
        for bad in ['-1','NaN','Infinity']:
            with self.assertRaises(ValueError): injection_budget(1, bad)

    def test_both_positions_consistent_and_direction_preserved(self):
        candidates, diagnostics = generate_candidates(self.graph, self.hubs)
        triples = {(c['source'],c['relation'],c['target']) for c in candidates}
        self.assertIn(('Q2','P26','Q1'), triples)
        self.assertIn(('Q2','P54','Q10'), triples)
        self.assertIn(('Q10','P286','Q2'), triples)
        self.assertFalse(any(r=='P54' and s=='Q10' for s,r,t in triples))
        self.assertEqual(diagnostics['accepted_unique'], len(candidates))

    def test_positive_qa_triple_original_and_duplicate_exclusion(self):
        forbidden = {('Q2','P54','Q10')}
        candidates, _ = generate_candidates(self.graph, {'Person':['Q1','Q2','Q3']}, forbidden)
        triples = [(c['source'],c['relation'],c['target']) for c in candidates]
        self.assertNotIn(('Q2','P54','Q10'), triples)
        self.assertNotIn(('Q1','P54','Q10'), triples)
        self.assertEqual(len(triples), len(set(triples)))

    def test_donor_relation_role_evidence_required(self):
        candidates, _ = generate_candidates(self.graph, {'Person':['Q1','Q3']})
        self.assertFalse(any(c['relation']=='P54' and c['source']=='Q3' for c in candidates))

    def test_quality_flags_and_cross_type_hubs_rejected(self):
        self.graph['nodes'][0]['general_type_annotation']['data_quality_flags'] = ['uncertain']
        with self.assertRaises(ValueError): generate_candidates(self.graph, self.hubs)
        with self.assertRaises(ValueError): generate_candidates(fixture(), {'Person':['Q1','Q10']})

    def test_qa_multiple_intermediates_no_false_second_hop_pairing(self):
        record = {'subject': {'subject':'Q1'}, 'relations':['P54','P286'],
                  'intermediate entities':[{'ID':'Q10'},{'ID':'Q11'}], 'answer annotations':[{'ID':'Q3'}]}
        positives = qa_positive_triples({'questions':[{'source_record':record}]})
        self.assertIn(('Q1','P54','Q10'), positives)
        self.assertNotIn(('Q10','P286','Q3'), positives)
        record['intermediate entities'].pop()
        self.assertIn(('Q10','P286','Q3'), qa_positive_triples({'questions':[{'source_record':record}]}))
        record['intermediate entities'].append({'ID':'Q10'})
        self.assertIn(('Q10','P286','Q3'), qa_positive_triples({'questions':[{'source_record':record}]}))

    def test_independent_validator_detects_altered_provenance(self):
        candidates, _ = generate_candidates(self.graph, self.hubs)
        injected = make_injected_edges(self.graph, balanced_sample(candidates, 2, 42))
        poisoned = augment_graph(self.graph, injected, {'configuration':{},'input_sha256':{}})
        self.assertTrue(validate_poisoned(self.graph, poisoned, self.hubs, 2)['passed'])
        broken = copy.deepcopy(poisoned)
        broken['edges'][-1]['injection_provenance']['original_relation'] = 'P999'
        with self.assertRaises(ValueError): validate_poisoned(self.graph, broken, self.hubs, 2)

    def test_zero_budget_is_empty_and_deterministic(self):
        candidates, _ = generate_candidates(self.graph, self.hubs)
        self.assertEqual(balanced_sample(candidates, 0, 42), [])
        self.assertEqual(generate_candidates(self.graph, self.hubs), generate_candidates(self.graph, self.hubs))

    def test_sampler_exhausted_small_buckets_do_not_starve_large_type(self):
        candidates = [{'source':f'Q{i+1}', 'relation':'P26' if i % 2 else 'P54',
                       'target':'Q99','entity_type':'Large' if i else 'Small'} for i in range(40)]
        selection = balanced_sample(candidates, 40, 42)
        self.assertEqual(len(selection), 40)
        self.assertEqual({(c['source'],c['relation'],c['target']) for c in selection},
                         {(c['source'],c['relation'],c['target']) for c in candidates})
        self.assertEqual(len(balanced_sample(candidates, 100, 42)), 40)

    def test_candidate_decisions_partition_all_pair_edge_attempts(self):
        candidates, diagnostics = generate_candidates(self.graph, {'Person':['Q1','Q2','Q3']})
        self.assertEqual(diagnostics['attempted'], len(candidates) + sum(diagnostics['rejected_by_reason'].values()))
        triples = [(c['source'],c['relation'],c['target']) for c in candidates]
        self.assertEqual(len(triples),len(set(triples)))

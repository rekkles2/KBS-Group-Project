import copy
import random
import unittest
from src.generate_candidates import generate_candidates
from src.inject_misinformation import make_injected_edges,augment_graph
from src.inject_misinformation import balanced_sample
from src.snapshot_visibility import snapshot_view,build_injection_visibility
from src.validate_poisoned import validate_poisoned
from tests.helpers import fixture


class RevisionSchemaTests(unittest.TestCase):
    def setUp(self):
        self.original=fixture();self.hubs={'Person':['Q1','Q2']}
        self.candidates=generate_candidates(self.original,self.hubs)[0]

    def graph(self,chosen):
        injected=make_injected_edges(self.original,chosen)
        return augment_graph(self.original,injected,{'configuration':{},'input_sha256':{}})

    def test_fake_labels_edges_and_separate_unresolved_truth(self):
        graph=self.graph(self.candidates)
        added=graph['edges'][len(self.original['edges']):]
        self.assertTrue(all(e['value']=='fake' and e['edge_origin']=='synthetic_injection' for e in added))
        self.assertTrue(all(e['factual_verification']['status']=='unresolved' for e in added))
        self.assertTrue(all(e['injection_provenance']['factual_verification_status']=='unverified' for e in added))
        self.assertEqual(graph['nodes'],self.original['nodes'])
        self.assertEqual(graph['edges'][:len(self.original['edges'])],self.original['edges'])

    def test_all_three_snapshots_activate_only_missing_observations(self):
        for n in self.original['nodes']:
            n['observed_in_snapshots']=['Dec2021','Dec2023','March2024']
        # Q2 is a real entity with no March observation; original incident edges
        # only visible Dec2021, while source Q1's edge is visible March2024 too.
        self.original['nodes'][1]['observed_in_snapshots']=['Dec2021','Dec2023']
        self.original['edges'][0]['observed_in_snapshots']=['Dec2021','March2024']
        chosen=[next(c for c in self.candidates if c['source']=='Q2' and c['relation']=='P54')]
        before=copy.deepcopy(self.original)
        graph=self.graph(chosen)
        self.assertEqual(graph['metadata']['task1_hub_injection']['injection_visibility']['March2024']['synthetically_visible_nodes'],['Q2'])
        self.assertEqual(graph['metadata']['task1_hub_injection']['injection_visibility']['Dec2021']['synthetically_visible_nodes'],[])
        march=snapshot_view(graph,'March2024')
        q2=next(n for n in march['nodes'] if n['record']['id']=='Q2')
        self.assertFalse(q2['originally_observed']);self.assertTrue(q2['synthetically_activated'])
        for snapshot in self.original['metadata']['snapshots']:
            view=snapshot_view(graph,snapshot);ids={n['record']['id'] for n in view['nodes']}
            self.assertTrue(all(e['record']['source'] in ids and e['record']['target'] in ids for e in view['edges']))
        self.assertEqual(before,self.original)

    def test_missing_overlay_activation_fails(self):
        graph=self.graph(self.candidates[:1])
        graph['metadata']['task1_hub_injection']['injection_visibility']['Dec2021']['synthetically_visible_nodes']=['Q999']
        with self.assertRaises(ValueError):snapshot_view(graph,'Dec2021')
        with self.assertRaises(ValueError):validate_poisoned(self.original,graph,self.hubs,1)

    def test_randomized_pairs_preserve_identity_and_renderability(self):
        rng=random.Random(602)
        for _ in range(30):
            chosen=rng.sample(self.candidates,rng.randrange(len(self.candidates)+1))
            graph=self.graph(chosen)
            self.assertTrue(validate_poisoned(self.original,graph,self.hubs,len(chosen))['passed'])

    def test_label_tamper_is_rejected(self):
        graph=self.graph(self.candidates[:1]);graph['edges'][-1]['value']='real'
        with self.assertRaises(ValueError):validate_poisoned(self.original,graph,self.hubs,1)

    def test_unsupported_factual_truth_tamper_is_rejected(self):
        graph=self.graph(self.candidates[:1])
        graph['edges'][-1]['factual_verification']['status']='verified_false'
        graph['edges'][-1]['factual_verification']['evidence_refs']=['unsupported-reference']
        with self.assertRaisesRegex(ValueError,'factual_verdicts_match_explicit_evidence_context'):
            validate_poisoned(self.original,graph,self.hubs,1)

    def test_presort_is_needed_for_input_order_independent_seed(self):
        candidates=[{'source':f'Q{i+1}','relation':'P26','target':'Q99','entity_type':'Person'} for i in range(12)]
        self.assertEqual(balanced_sample(candidates,5,42),balanced_sample(candidates[::-1],5,42))

    def test_every_accepted_candidate_has_a_changed_position(self):
        self.assertTrue(all(c['changed_positions'] for c in self.candidates))

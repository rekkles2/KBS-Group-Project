import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.factual_verification import annotate_factual_verification
from tests.helpers import fixture


class FactualVerificationTests(unittest.TestCase):
    def setUp(self):
        self.original = fixture()
        self.injected = [{'source': 'Q1', 'relation': 'P54', 'target': 'Q11',
                          'injection_provenance': {'factual_verification_status': 'unverified', 'source_edge_index': 0}}]

    def record(self, status='verified_true', **changes):
        value = {'triple': ['Q1', 'P54', 'Q11'], 'status': status,
                 'independently_reviewed': True, 'direct_claim_evidence': True,
                 'scope_matches_claim': True, 'evidence_refs': ['fixture:authoritative_direct_claim'],
                 'temporal_scope': 'Illustrative test claim with explicitly reviewed historical interval 2020-2022.',
                 'reason': 'Fixture only; direct source supports the exact scoped claim.'}
        value.update(changes)
        return value

    def annotate_records(self, records):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'reviewed.json'
            path.write_text(json.dumps({'records': records}), encoding='utf-8')
            return annotate_factual_verification(self.original, self.injected, path)

    def test_absence_and_alternative_object_are_not_false(self):
        before = copy.deepcopy(self.original)
        result = annotate_factual_verification(self.original, self.injected)
        self.assertEqual(result['unresolved'], 1)
        self.assertEqual(self.original, before)
        self.assertEqual(self.injected[0]['injection_provenance']['factual_verification_status'], 'unverified')

    def test_independently_reviewed_direct_positive_can_support_true(self):
        self.assertEqual(self.annotate_records([self.record()])['verified_true'], 1)

    def test_direct_contradiction_requires_reviewed_matching_scope(self):
        self.assertEqual(self.annotate_records([self.record('verified_false')])['verified_false'], 1)
        self.assertEqual(self.annotate_records([self.record('verified_false', scope_matches_claim=False)])['unresolved'], 1)

    def test_unreviewed_model_output_and_raw_statement_are_not_ground_truth(self):
        self.assertEqual(self.annotate_records([self.record(independently_reviewed=False)])['unresolved'], 1)
        self.assertEqual(self.annotate_records([self.record(direct_claim_evidence=False)])['unresolved'], 1)

    def test_conflicting_reviewed_sources_remain_unresolved(self):
        self.assertEqual(self.annotate_records([self.record(), self.record('verified_false')])['unresolved'], 1)

    def test_wrong_triple_and_missing_scope_remain_unresolved(self):
        self.assertEqual(self.annotate_records([self.record(triple=['Q2', 'P54', 'Q11'])])['unresolved'], 1)
        self.assertEqual(self.annotate_records([self.record(temporal_scope='')])['unresolved'], 1)

    def test_local_annotation_match_is_recorded_separately_from_historical_truth(self):
        self.injected[0]['target'] = 'Q10'
        result = annotate_factual_verification(self.original, self.injected)
        self.assertTrue(self.injected[0]['factual_verification']['original_graph_match'])
        self.assertEqual(result['unresolved'], 1)

    def test_annotation_roundtrip_is_deterministic_and_preserves_provenance(self):
        provenance = copy.deepcopy(self.injected[0]['injection_provenance'])
        annotate_factual_verification(self.original, self.injected)
        first = json.dumps(self.injected, sort_keys=True)
        annotate_factual_verification(self.original, self.injected)
        self.assertEqual(first, json.dumps(self.injected, sort_keys=True))
        self.assertEqual(json.loads(first)[0]['injection_provenance'], provenance)


if __name__ == '__main__':
    unittest.main()

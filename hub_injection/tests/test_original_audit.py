import copy
import os
from pathlib import Path
import unittest
from src.load_data import load_data
from src.validate_original import validate_original

DATA = Path(os.environ.get('PAT_KG_INPUT_DIR',Path(__file__).resolve().parents[3]))


class OriginalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph, cls.rows, _ = load_data(DATA/'pat_kg_merged.json', DATA/'entity_id_value_type.csv')

    def test_complete_audit_and_known_annotation_duplicates(self):
        audit = validate_original(self.graph, self.rows)
        self.assertEqual(audit['discrepancies'], {})
        self.assertEqual(audit['qa_positive_triples'], 7738)
        self.assertEqual(audit['qa_records_with_duplicate_intermediate_qids'], 20)

    def test_csv_type_disagreement_is_error(self):
        rows = [dict(r) for r in self.rows]
        rows[0]['entity_type'] = 'WrongType'
        with self.assertRaisesRegex(ValueError, 'Node/CSV disagreement'):
            validate_original(self.graph, rows)

    def test_duplicate_original_triple_is_error(self):
        graph = dict(self.graph)
        graph['edges'] = self.graph['edges'] + [self.graph['edges'][0]]
        with self.assertRaisesRegex(ValueError, 'unique_original_triples'):
            validate_original(graph, self.rows)

    def test_dangling_edge_endpoint_is_error(self):
        graph = dict(self.graph)
        graph['edges'] = list(self.graph['edges'])
        graph['edges'][0] = {**graph['edges'][0], 'source':'Q99999999999999999999999'}
        with self.assertRaisesRegex(ValueError, 'Dangling original edge'):
            validate_original(graph, self.rows)

    def test_wrong_qa_hop_reference_is_error(self):
        graph = dict(self.graph)
        graph['edges'] = list(self.graph['edges'])
        graph['edges'][0] = copy.deepcopy(graph['edges'][0])
        graph['edges'][0]['evidence'][0]['question_id'] = 'missing-question'
        with self.assertRaisesRegex(ValueError, 'Invalid evidence reference'):
            validate_original(graph, self.rows)

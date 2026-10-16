"""Run the real CLI in three fresh stdlib-only subprocesses and compare bytes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from src.load_data import sha256

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('PAT_KG_INPUT_DIR', ROOT.parents[1]))


class ActualDatasetIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix='pat-task1-')
        cls.results = []
        cls.runs = []
        cls.before = {name: sha256(DATA / name) for name in ['pat_kg_merged.json','entity_id_value_type.csv']}
        for i, seed in enumerate([42,42,43]):
            destination = Path(cls.directory.name) / str(i)
            # -E ignores Python env configuration; -S skips site-packages.
            process = subprocess.run([sys.executable,'-E','-S',str(ROOT/'run_task1.py'),
                '--graph',str(DATA/'pat_kg_merged.json'),'--entities',str(DATA/'entity_id_value_type.csv'),
                '--work-dir',str(destination),'--seed',str(seed)], cwd=cls.directory.name,
                capture_output=True, text=True, encoding='utf-8', timeout=180)
            if process.returncode:
                cls.directory.cleanup()
                raise AssertionError(f'Clean-process run failed: {process.stdout}\n{process.stderr}')
            cls.results.append(json.loads(process.stdout))
            cls.runs.append(destination)

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_actual_dataset_counts(self):
        for result in self.results:
            self.assertEqual(result['nodes'],7868)
            self.assertEqual(result['original_edges'],7737)
            self.assertEqual(result['injected_edges'],774)
            self.assertEqual(result['total_edges'],8511)
            self.assertEqual(result['status'],'PASS')

    def test_same_seed_all_outputs_identical_bytes(self):
        first = self.runs[0] / 'outputs'
        for path in first.iterdir():
            self.assertEqual(sha256(path), sha256(self.runs[1] / 'outputs' / path.name), path.name)
        for path in (self.runs[0]/'reports').iterdir():
            self.assertEqual(sha256(path), sha256(self.runs[1] / 'reports' / path.name), path.name)

    def test_alternative_seed_changes_valid_selection(self):
        self.assertNotEqual(sha256(self.runs[0]/'outputs/injected_edges.jsonl'),
                            sha256(self.runs[2]/'outputs/injected_edges.jsonl'))
        for destination in self.runs:
            validation = json.loads((destination/'reports/validation_results.json').read_text(encoding='utf-8'))
            self.assertTrue(validation['passed'])
            self.assertTrue(validation['original_input_checksums_unchanged'])

    def test_inputs_untouched_after_repeated_runs(self):
        self.assertEqual(self.before, {name:sha256(DATA/name) for name in self.before})

    def test_serialized_preservation_of_every_original_object(self):
        original = json.loads((DATA/'pat_kg_merged.json').read_text(encoding='utf-8-sig'))
        augmented = json.loads((self.runs[0]/'outputs/pat_kg_poisoned_10pct.json').read_text(encoding='utf-8'))
        for field in ['nodes','relations','questions','unresolved_paths']:
            self.assertEqual(original[field],augmented[field])
        self.assertEqual(original['edges'],augmented['edges'][:7737])
        for key,value in original['metadata'].items():
            self.assertEqual(value,augmented['metadata'][key])

"""Check portable packaging isolation and independent chart calculations."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.package_release_v2 import package
from tools.audit_visuals_v2 import audit_chart
from src.report_statistics import bar_chart


class PortableTests(unittest.TestCase):
    def test_package_omits_credentials_and_caches_but_hashes_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'project'
            (root / 'src').mkdir(parents=True)
            (root / '.opencode-local').mkdir()
            (root / 'src/main.py').write_text('print(1)')
            (root / 'api_key.txt').write_text('test-fixture-secret')
            (root / '.opencode-local/private').write_text('test-fixture-secret')
            (root / 'src/cache.pyc').write_bytes(b'cache')
            graph, entities = base / 'graph.json', base / 'entities.csv'
            graph.write_text('{}')
            entities.write_text('id,type\n')
            result = package(root, base / 'release.zip', graph, entities)
            with zipfile.ZipFile(result['archive']) as archive:
                names = archive.namelist()
                self.assertEqual(set(names), {'task1_hub_injection/src/main.py',
                                             'task1_hub_injection/PORTABLE_MANIFEST.json'})
                manifest = json.loads(archive.read('task1_hub_injection/PORTABLE_MANIFEST.json'))
                self.assertFalse(manifest['original_inputs_included'])
                self.assertEqual(len(manifest['required_inputs']), 2)
                self.assertEqual(manifest['required_inputs'][0]['filename'], 'graph.json')
            with self.assertRaises(FileExistsError):
                package(root, base / 'release.zip', graph, entities)

    def test_chart_audit_rejects_wrong_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'chart.svg'
            bar_chart(path, 'Fixture', {'P1': 3, 'P2': 1})
            self.assertEqual(audit_chart(path, {'P1': 3, 'P2': 1})['total'], 4)
            with self.assertRaises(AssertionError):
                audit_chart(path, {'P1': 2, 'P2': 1})


if __name__ == '__main__':
    unittest.main()

"""Execute unittest and save actual machine-readable and textual results."""
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), top_level_dir=str(ROOT))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    log = stream.getvalue()
    (ROOT / 'reports/tests.log').write_text(log, encoding='utf-8')
    summary = {'tests_run':result.testsRun, 'failures':len(result.failures), 'errors':len(result.errors),
               'skipped':len(result.skipped), 'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
               'successful':result.wasSuccessful()}
    (ROOT / 'reports/tests_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(log)
    print(json.dumps(summary))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())

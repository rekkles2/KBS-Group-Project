"""Build an explicit, credential-free portable ZIP with separate-input manifest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {'__pycache__', '.git', '.pytest_cache', '.opencode-local',
                  'releases', '.playwright-cli', 'node_modules'}
SECRET_NAMES = {'api_key.txt', 'opencode_model.txt', 'opencode_model.original.txt', '.env'}
RUNTIME_DIRS = {'src', 'tests', 'config', 'tools', 'outputs', 'reports', 'output'}


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def included(path, root):
    rel = path.relative_to(root)
    return (not EXCLUDED_PARTS.intersection(rel.parts)
            and path.name.lower() not in SECRET_NAMES
            and path.suffix.lower() not in {'.zip', '.pyc', '.pyo'}
            and (len(rel.parts) == 1 or rel.parts[0] in RUNTIME_DIRS))


def package(root, destination, graph, entities):
    root, destination = Path(root).resolve(), Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f'Refusing to overwrite release: {destination}')
    manifest = {
        'format': 'task1-portable-v2', 'python_packager': platform.python_version(),
        'required_python': '>=3.10', 'runtime_dependencies': 'Python standard library',
        'original_inputs_included': False,
        'required_inputs': [
            {'argument': arg, 'filename': Path(path).name,
             'bytes': Path(path).stat().st_size, 'sha256': sha256(path)}
            for arg, path in [('--graph', graph), ('--entities', entities)]],
        'excluded': sorted(EXCLUDED_PARTS | SECRET_NAMES | {'*.zip', '*.pyc', '*.pyo'}),
        'credential_policy': 'Explicit filename/path exclusions; local credentials never needed to regenerate graph.',
        'files': {}}
    paths = [p for p in sorted(root.rglob('*')) if p.is_file() and included(p, root) and p != destination]
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            rel = path.relative_to(root).as_posix()
            manifest['files'][rel] = {'bytes': path.stat().st_size, 'sha256': sha256(path)}
            archive.write(path, 'task1_hub_injection/' + rel)
        archive.writestr('task1_hub_injection/PORTABLE_MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    return {'archive': str(destination), 'sha256': sha256(destination), 'files': len(paths),
            'required_inputs': manifest['required_inputs']}


def check_clean_regeneration(root, graph, entities, evidence):
    """Copy code and actual inputs; start with absent outputs, run twice and test."""
    root = Path(root).resolve()
    with tempfile.TemporaryDirectory(prefix='task1-portable-') as temporary:
        stage = Path(temporary)
        code, inputs = stage / 'package', stage / 'supplied_inputs'
        code.mkdir()
        inputs.mkdir()
        for path in root.rglob('*'):
            rel = path.relative_to(root)
            if not path.is_file() or not included(path, root):
                continue
            if rel.parts[0] in {'outputs', 'reports', 'output'}:
                continue
            target = code / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        for path, name in [(graph, 'pat_kg_merged.json'), (entities, 'entity_id_value_type.csv')]:
            shutil.copyfile(path, inputs / name)
        (code / 'reports').mkdir()
        runs, logs = [], []
        for i in range(2):
            destination = stage / f'run_{i}'
            assert not destination.exists(), 'Clean output precondition failed'
            command = [sys.executable, str(code / 'run_task1.py'), '--graph',
                       str(inputs / 'pat_kg_merged.json'), '--entities',
                       str(inputs / 'entity_id_value_type.csv'), '--work-dir',
                       str(destination), '--seed', '42']
            process = subprocess.run(command, cwd=code, capture_output=True,
                                     text=True, encoding='utf-8')
            logs.append({'command': ['python', 'run_task1.py', '--graph', '<supplied-inputs>/pat_kg_merged.json',
                                     '--entities', '<supplied-inputs>/entity_id_value_type.csv',
                                     '--work-dir', f'<new-run-{i}>', '--seed', '42'],
                         'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr})
            if process.returncode:
                raise RuntimeError(f'Clean regeneration failed: {process.stderr}')
            runs.append({p.name: sha256(p) for p in sorted((destination / 'outputs').iterdir()) if p.is_file()})
        environment = {**os.environ, 'PAT_KG_INPUT_DIR': str(inputs)}
        tests = subprocess.run([sys.executable, 'run_tests.py'], cwd=code, env=environment,
                               text=True, encoding='utf-8', capture_output=True)
        canonical = {name: sha256(root / 'outputs' / name) for name in runs[0]}
        result = {'python': platform.python_version(), 'platform': platform.platform(),
                  'runtime_dependencies': 'Python standard library',
                  'fresh_independent_code_and_input_copies': True,
                  'preexisting_outputs_or_cache_copied': False,
                  'hardlinks_used': False,
                  'run_output_sha256': runs, 'canonical_output_sha256': canonical,
                  'two_clean_runs_byte_identical': runs[0] == runs[1],
                  'clean_run_matches_delivered_outputs': runs[0] == canonical,
                  'run_logs': logs, 'tests_exit_code': tests.returncode,
                  'tests_stdout': tests.stdout, 'tests_stderr': tests.stderr}
        Path(evidence).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        if tests.returncode or runs[0] != runs[1] or runs[0] != canonical:
            raise AssertionError('Portable reproduction comparison/test failed; see evidence JSON')
        return {'clean_regeneration': 'PASS', 'outputs_compared': len(canonical),
                'evidence': str(evidence)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--graph', type=Path, required=True)
    parser.add_argument('--entities', type=Path, required=True)
    parser.add_argument('--check-clean', type=Path, help='Save clean regeneration/test evidence JSON')
    args = parser.parse_args()
    if args.check_clean:
        print(json.dumps(check_clean_regeneration(args.root, args.graph, args.entities, args.check_clean), indent=2))
    if args.destination:
        print(json.dumps(package(args.root, args.destination, args.graph, args.entities), indent=2))
    if not args.check_clean and not args.destination:
        parser.error('Provide --destination or --check-clean')


if __name__ == '__main__':
    main()

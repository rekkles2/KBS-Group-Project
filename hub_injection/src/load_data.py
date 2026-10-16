"""Read input objects without mutating or duplicating source files."""
import csv
import hashlib
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_data(graph_path, csv_path):
    with Path(graph_path).open(encoding='utf-8-sig') as stream:
        graph = json.load(stream)
    with Path(csv_path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    return graph, rows, {'graph': sha256(graph_path), 'entity_csv': sha256(csv_path)}


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def triple(edge):
    return edge['source'], edge['relation'], edge['target']

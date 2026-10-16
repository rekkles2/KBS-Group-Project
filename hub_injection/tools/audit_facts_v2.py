"""Audit every injected claim locally and selectively retrieve raw Wikidata claims.

No truth label is inferred from claim absence, alternative objects, or API errors.
Use --fetch for a bounded, systematic 40-subject sample covering every relation.
"""
import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.request
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.factual_verification import annotate_factual_verification
from src.load_data import triple


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sample_subjects(edges, limit=40):
    chosen = []
    for relation in sorted({e['relation'] for e in edges}):
        subject = min(e['source'] for e in edges if e['relation'] == relation)
        if subject not in chosen:
            chosen.append(subject)
    for subject in sorted({e['source'] for e in edges}):
        if subject not in chosen and len(chosen) < limit:
            chosen.append(subject)
    return chosen


def fetch(subjects, cache):
    logs = []
    for start in range(0, len(subjects), 10):
        batch = subjects[start:start + 10]
        params = {'action': 'wbgetentities', 'format': 'json', 'props': 'claims|info', 'ids': '|'.join(batch)}
        url = 'https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode(params)
        entry = {'url': url, 'subjects': batch, 'requested_at_utc': datetime.now(timezone.utc).isoformat(),
                 'timeout_seconds': 12, 'cache_file': f'batch_{start // 10:02d}.json'}
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'PAT-KG-Research-Audit/2.0 (selective factual audit)', 'Accept': 'application/json'})
            with urllib.request.urlopen(request, timeout=12) as response:
                raw = response.read()
                entry['http_status'] = response.status
            entry['sha256'] = hashlib.sha256(raw).hexdigest()
            (cache / entry['cache_file']).write_bytes(raw)
            data = json.loads(raw)
            entry['success'] = bool(data.get('entities'))
            if not entry['success']:
                entry['error'] = str(data.get('error', 'No entities returned'))
        except Exception as error:
            entry.update(success=False, error=f'{type(error).__name__}: {error}')
            write(cache / entry['cache_file'], {'request': url, 'error': entry['error']})
        logs.append(entry)
        write(cache / 'request_log.json', logs)
        time.sleep(1)
    return logs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, default=ROOT.parents[1] / 'pat_kg_merged.json')
    parser.add_argument('--graph', type=Path, default=ROOT.parent / 'pat_kg_poisoned_10pct.json')
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    out = ROOT / 'reports/revision_audit'
    cache = out / 'evidence_cache'
    cache.mkdir(parents=True, exist_ok=True)
    original = json.loads(args.original.read_text(encoding='utf-8'))
    graph = json.loads(args.graph.read_text(encoding='utf-8'))
    edges = [e for e in graph['edges'] if e.get('edge_origin') == 'synthetic_injection']
    statuses = annotate_factual_verification(original, edges)
    subjects = sample_subjects(edges)
    write(cache / 'sampling_plan.json', {'method': 'One lexically first subject per relation, then lexical fill to 40 unique subjects; purposive coverage, not random population inference.', 'subjects': subjects,
                                       'sample_relation_ids': sorted({e['relation'] for e in edges if e['source'] in subjects})})
    if args.fetch:
        fetch(subjects, cache)
    logs_path = cache / 'request_log.json'
    logs = json.loads(logs_path.read_text(encoding='utf-8')) if logs_path.exists() else []
    entities = {}
    subject_refs = {}
    for entry in logs:
        if entry.get('success'):
            payload = json.loads((cache / entry['cache_file']).read_text(encoding='utf-8'))
            entities.update(payload.get('entities', {}))
            subject_refs.update({s: entry['cache_file'] for s in payload.get('entities', {})})
    rows = []
    for edge in edges:
        a = edge['factual_verification']
        claims = entities.get(edge['source'], {}).get('claims', {}).get(edge['relation'], [])
        matches = [c for c in claims if c.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id') == edge['target']]
        attempted = any(edge['source'] in entry['subjects'] for entry in logs)
        references = list(a['evidence_refs'])
        if edge['source'] in subject_refs:
            references.append('evidence_cache/' + subject_refs[edge['source']])
        row = {'source': edge['source'], 'relation': edge['relation'], 'target': edge['target'],
               'status': a['status'], 'legacy_status': edge['injection_provenance']['factual_verification_status'],
               'verification_method': a['method'] + ('; raw_Wikidata_claim_comparison' if edge['source'] in entities else ''),
               'evidence_refs': json.dumps(references), 'temporal_scope': a['temporal_scope'], 'reason': a['reason'],
               'relation_cardinality': a['relation_cardinality'], 'original_graph_match': a['original_graph_match'],
               'original_qa_match': a['original_qa_match'], 'external_subject_attempted': attempted,
               'external_subject_retrieved': edge['source'] in entities, 'raw_identical_claim_count': len(matches),
               'raw_matching_statement_ids': json.dumps([m.get('id') for m in matches]),
               'raw_matching_qualifiers': json.dumps([m.get('qualifiers', {}) for m in matches]),
               'raw_matching_reference_counts': json.dumps([len(m.get('references', [])) for m in matches])}
        if matches:
            row['reason'] += ' Raw matching Wikidata statements require reference and temporal-scope adjudication; retrieval alone does not establish historical truth.'
        rows.append(row)
    with (out / 'factual_verification.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {'injected_edges_audited': len(edges), 'statuses': statuses, 'local_original_graph_matches': sum(r['original_graph_match'] for r in rows),
               'local_QA_matches': sum(r['original_qa_match'] for r in rows), 'total_relations': len({e['relation'] for e in edges}),
               'selected_subjects': len(subjects), 'external_requests': len(logs), 'successful_requests': sum(e['success'] for e in logs),
               'retrieved_subjects': len(entities), 'externally_covered_edges': sum(r['external_subject_retrieved'] for r in rows),
               'edges_with_raw_identical_claim': sum(bool(r['raw_identical_claim_count']) for r in rows),
               'errors': [e['error'] for e in logs if not e['success']]}
    write(out / 'factual_verification_statistics.json', summary)
    text = '# Factual verification audit\n\n```json\n' + json.dumps(summary, indent=2) + '\n```\n\n'
    text += ('All injected claims were compared exactly with every original graph edge and conservatively projectable PAT QA positive. '
             'No missing claim, alternative object, node type, high degree or synthetic label is evidence of falsity. '
             'The canonical generator records unresolved independently of network results and preserves legacy unverified metadata.\n\n'
             'External coverage uses a purposive 40-subject sample covering all injected relations, not a random statistical sample. '
             'Four batched Wikidata API requests use a 12 second timeout and at least one second between requests; raw successful responses and errors are cached. '
             'Only actual successful retrievals count toward external coverage; failed attempts do not. No API keys are used. '
             'Raw statement IDs, references and qualifiers are retained, but no automatic historical truth conclusion follows from current statements. '
             'No independently reviewed direct-claim evidence cache was supplied. No model assessment supplies ground truth.\n\n'
             'Every relation is treated as potentially multivalued or time/context dependent until a claim-specific constraint is established. '
             'P54, P69, P286, P39 and P26 are not treated as globally functional. Snapshot visibility denotes an experimental overlay and QA observation, not a historical validity interval. '
             'No verified misinformation subset can be claimed when verified_false is zero.\n\n'
             'Wikidata documentation confirms optional qualifiers/references and multivalued statements: '
             '[Statements](https://www.wikidata.org/wiki/Help:Statements), [Qualifiers](https://www.wikidata.org/wiki/Help:Qualifiers). '
             'These documentation pages were independently read; they are semantic guidance, not evidence for any injected triple.\n\n'
             'Reproduce offline: `python tools/audit_facts_v2.py`. Refresh bounded live requests: `python tools/audit_facts_v2.py --fetch`. '
             'Refreshing intentionally updates evidence request timestamps; the canonical dataset generation remains offline and deterministic.\n')
    (out / 'factual_verification_summary.md').write_text(text, encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

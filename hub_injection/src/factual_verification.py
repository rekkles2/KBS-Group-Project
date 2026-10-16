"""Conservative, offline, deterministic claim annotations; no closed-world inference.

An optional JSON evidence cache must contain independently reviewed claim records.
Raw Wikidata API responses are not adjudicated evidence and cannot change truth labels.
"""
import json
from collections import Counter
from pathlib import Path
from .load_data import triple
from .validate_original import qa_positive_triples

CARDINALITY = ('Potentially multivalued or time/context dependent; no relation-specific '
               'functional or exclusivity constraint has been established for this claim.')


def _usable(record, key):
    return (tuple(record.get('triple', ())) == key
            and record.get('status') in {'verified_true', 'verified_false'}
            and record.get('independently_reviewed') is True
            and record.get('direct_claim_evidence') is True
            and record.get('evidence_refs')
            and record.get('temporal_scope')
            and record.get('scope_matches_claim') is True
            and record.get('reason'))


def annotate_factual_verification(original, injected, evidence_cache_path=None):
    """Annotate injected edges in place and return status counts.

    Default annotations describe a truth audit, not inferred falsity. Original KG
    and QA matches are recorded as positive annotation support, never mistaken for
    independent historical verification. Explicit reviewed evidence must match the
    exact triple and claim scope; conflicting verdicts remain unresolved.
    Legacy provenance is never changed. No network access occurs here.
    """
    records = []
    if evidence_cache_path is not None:
        records = json.loads(Path(evidence_cache_path).read_text(encoding='utf-8')).get('records', [])
    original_triples = {triple(edge) for edge in original['edges']}
    positives = qa_positive_triples(original)
    counts = Counter()
    for edge in injected:
        key = triple(edge)
        local = []
        if key in original_triples:
            local.append('original_graph:identical_triple')
        if key in positives:
            local.append('original_PAT_QA:identical_conservative_projection')
        annotation = {'status': 'unresolved', 'method': 'exact_original_KG_and_PAT_QA_audit',
                      'evidence_refs': local, 'temporal_scope': 'Historical fact-validity interval unknown; synthetic snapshot visibility is not a truth interval.',
                      'reason': 'No independently adjudicated direct supporting or contradicting evidence. Absence is not falsity.',
                      'relation_cardinality': CARDINALITY,
                      'original_graph_match': key in original_triples, 'original_qa_match': key in positives}
        matches = [record for record in records if _usable(record, key)]
        verdicts = {record['status'] for record in matches}
        if len(verdicts) == 1:
            annotation.update(status=matches[0]['status'], method='explicit_independently_reviewed_direct_claim_evidence',
                              evidence_refs=sorted({ref for record in matches for ref in record['evidence_refs']}),
                              temporal_scope=matches[0]['temporal_scope'], reason=matches[0]['reason'])
        elif len(verdicts) > 1:
            annotation.update(reason='Conflicting directly reviewed evidence; unresolved pending adjudication.',
                              evidence_refs=sorted({ref for record in matches for ref in record['evidence_refs']}))
        edge['factual_verification'] = annotation
        counts[annotation['status']] += 1
    return {key: counts[key] for key in ('verified_false', 'verified_true', 'unresolved')}

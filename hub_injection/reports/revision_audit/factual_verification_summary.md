# Factual verification audit

```json
{
  "injected_edges_audited": 774,
  "statuses": {
    "verified_false": 0,
    "verified_true": 0,
    "unresolved": 774
  },
  "local_original_graph_matches": 0,
  "local_QA_matches": 0,
  "total_relations": 18,
  "selected_subjects": 40,
  "external_requests": 4,
  "successful_requests": 4,
  "retrieved_subjects": 40,
  "externally_covered_edges": 86,
  "edges_with_raw_identical_claim": 0,
  "errors": []
}
```

All injected claims were compared exactly with every original graph edge and conservatively projectable PAT QA positive. No missing claim, alternative object, node type, high degree or synthetic label is evidence of falsity. The canonical generator records unresolved independently of network results and preserves legacy unverified metadata.

External coverage uses a purposive 40-subject sample covering all injected relations, not a random statistical sample. Four batched Wikidata API requests use a 12 second timeout and at least one second between requests; raw successful responses and errors are cached. Only actual successful retrievals count toward external coverage; failed attempts do not. No API keys are used. Raw statement IDs, references and qualifiers are retained, but no automatic historical truth conclusion follows from current statements. No independently reviewed direct-claim evidence cache was supplied. No model assessment supplies ground truth.

Every relation is treated as potentially multivalued or time/context dependent until a claim-specific constraint is established. P54, P69, P286, P39 and P26 are not treated as globally functional. Snapshot visibility denotes an experimental overlay and QA observation, not a historical validity interval. No verified misinformation subset can be claimed when verified_false is zero.

Wikidata documentation confirms optional qualifiers/references and multivalued statements: [Statements](https://www.wikidata.org/wiki/Help:Statements), [Qualifiers](https://www.wikidata.org/wiki/Help:Qualifiers). These documentation pages were independently read; they are semantic guidance, not evidence for any injected triple.

Reproduce offline: `python tools/audit_facts_v2.py`. Refresh bounded live requests: `python tools/audit_facts_v2.py --fetch`. Refreshing intentionally updates evidence request timestamps; the canonical dataset generation remains offline and deterministic.

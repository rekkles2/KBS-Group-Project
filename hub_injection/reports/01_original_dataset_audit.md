# Original dataset audit

All listed checks were executed before candidate generation.

```json
{
  "input_sha256": {
    "graph": "f5a1c2f4b556bf060e89540ab1b5c05f836afe29cc0f13cdcd80f92120171f31",
    "entity_csv": "c653dde9d87f61295dac67aac1151d5510c7d6b9c0081ada82b31ea1f053be2e"
  },
  "checks": {
    "unique_qids": true,
    "valid_qids": true,
    "unique_relations": true,
    "valid_relations": true,
    "unique_qa_ids": true,
    "unique_original_triples": true,
    "csv_unique_qids": true,
    "csv_node_coverage": true,
    "known_snapshot_ids": true,
    "all_node_csv_types_eligibility_flags_consistent": true,
    "original_endpoints_relations_evidence_snapshots_valid": true,
    "qa_snapshot_ids": true,
    "unresolved_qa_references": true,
    "metadata_snapshot_semantics": true,
    "metadata_node_snapshot_semantics": true,
    "metadata_projection_semantics": true,
    "metadata_pairing_policy": true
  },
  "counts": {
    "nodes": 7868,
    "edges": 7737,
    "relations": 20,
    "questions": 18436,
    "unresolved_paths": 496
  },
  "expected_counts": {
    "nodes": 7868,
    "edges": 7737,
    "relations": 20,
    "questions": 18436,
    "unresolved_paths": 496
  },
  "discrepancies": {},
  "qa_positive_triples": 7738,
  "flag_counts": {
    "insufficient_type_evidence": 2,
    "source_label_mismatch": 1,
    "education_level_unverified": 11,
    "education_entity_identity_unverified": 2,
    "role_based_interpretation_unverified": 2,
    "source_qid_mismatch": 1
  },
  "qa_records_with_duplicate_intermediate_qids": 20
}
```

The graph is a directed multirelational QA annotation projection, not reconstructed temporal Wikidata.

**snapshot_semantics**: Annotation observation, not fact validity interval.

**node_snapshot_semantics**: Occurrence as subject, intermediate, or answer in any retained source QA record, including records excluded from edge projection; not existence or validity dates.

**projection_semantics**: QA paths projected to entity edges; Wikidata statement qualifiers and temporal ordering are not reconstructed.

**pairing_policy**: For multiple intermediate entities retain first-hop edges; do not infer second-hop pairings.

Full degree, relation, type and snapshot distributions: original_statistics.json.

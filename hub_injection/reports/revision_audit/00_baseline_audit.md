# Baseline v1 audit

Backup is an independent byte copy, not a hard link.

```json
{
  "timestamp": "20261016T103451+0900",
  "backup_directory": "D:\\\u5b66\u4e60\\KBS_project\\new_KG\\releases\\baseline_v1_20261016T103451+0900",
  "counts": {
    "nodes": 7868,
    "relations": 20,
    "edges": 7737,
    "questions": 18436,
    "unresolved_paths": 496
  },
  "augmented_edges": 8511,
  "synthetic_edges": 774,
  "synthetic_fake_labels": 0,
  "checks": {
    "original_edge_prefix": true,
    "original_metadata": true,
    "nodes": true,
    "relations": true,
    "questions": true,
    "unresolved_paths": true,
    "backup_independent": true,
    "backup_hash_match": true
  },
  "snapshot_mismatches": {
    "Dec2021": {
      "injected_visible": 642,
      "both_originally_observed": 623,
      "violating_edges": 19
    },
    "Dec2023": {
      "injected_visible": 649,
      "both_originally_observed": 643,
      "violating_edges": 6
    },
    "March2024": {
      "injected_visible": 609,
      "both_originally_observed": 590,
      "violating_edges": 19
    }
  },
  "distinct_visibility_mismatches": 38,
  "figures": [
    "reports\\injected_by_relation.svg",
    "reports\\injected_by_type.svg"
  ],
  "hashes": {
    "pat_kg_merged.json": "f5a1c2f4b556bf060e89540ab1b5c05f836afe29cc0f13cdcd80f92120171f31",
    "entity_id_value_type.csv": "c653dde9d87f61295dac67aac1151d5510c7d6b9c0081ada82b31ea1f053be2e",
    "new_KG\\pat_kg_poisoned_10pct.json": "20d1d60116eb8ce3306f879e5c0745174a1352efdf82e534d7562228cbc85467",
    "new_KG.zip": "d66b4343b313ae6ca691238097e89d02627f5c0fa4467f6ec2758825f3646c7b"
  }
}
```

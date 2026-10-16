# PAT-KG data reference

This reference describes the JSON and CSV files delivered in this repository. Field names are case-sensitive. The graph is a directed, multi-relational projection of PAT-Questions annotations. Snapshot membership records annotation observations or synthetic display visibility, depending on the record's origin; it does not specify real-world fact-validity intervals.

## Graph files and top-level fields

`original_KG/pat_kg_merged.json` is the source graph. `pat_kg_poisoned_10pct.json` is the augmented graph; its byte-identical pipeline copy is `hub_injection/outputs/pat_kg_poisoned_10pct.json`.

| Field | Type | Contents |
|---|---|---|
| `metadata` | object | Source provenance, snapshot semantics, entity-type policy and statistics |
| `nodes` | array of objects | 7,868 original Wikidata entities |
| `relations` | array of objects | 20 Wikidata properties, identified by `id` |
| `edges` | array of objects | 7,737 original directed triples; the augmented graph appends 774 synthetic triples |
| `questions` | array of objects | 18,436 source QA annotation records, preserved in the augmented graph |
| `unresolved_paths` | array of objects | 496 QA projection issues, preserved for inspection |

`metadata.stats` describes the original graph. Use `metadata.task1_hub_injection.augmented_statistics` for augmented counts. Historical source-directory and archive paths are provenance strings, not required local paths.

## Nodes

| Field | Meaning |
|---|---|
| `id` | Wikidata QID; joins to edge endpoints and label-table `qid` |
| `labels` | Array of available entity labels |
| `entity_type` | Reviewed general entity type used for swap compatibility |
| `observed_in_snapshots` | Original QA observation snapshots |
| `detailed_entity_types` | Wikidata `P31` classes with available IDs, labels, ranks and statement IDs |
| `subclass_of` | Available `P279` annotations |
| `type_annotation` | Typing source, retrieval time and scope; live typing is not historical snapshot evidence |
| `general_type_annotation` | Type-policy decision, class mappings, quality flags and `eligible_for_type_swap` |

The pipeline preserves every original node object. It creates no entity nodes, and synthetic-edge participation does not make an entity fictitious.

## Original edges

| Field | Meaning |
|---|---|
| `source`, `relation`, `target` | Directed `(QID, property ID, QID)` triple |
| `observed_in_snapshots` | Snapshots whose QA annotations project to this triple |
| `evidence` | Array of `{question_id, hop}` references to source QA records |

Triples are unique across the merged graph; their snapshot lists can contain multiple observations. The first 7,737 entries of the augmented `edges` array preserve the original edge objects and order. Original edges need not have `edge_origin`, `value` or `is_poisoned` fields.

## Synthetic edges

Synthetic records retain the triple fields and add the following fields:

| Field | Meaning |
|---|---|
| `edge_origin` | `"synthetic_injection"`; canonical marker for synthetic display styling |
| `value` | `"fake"`; construction class, not a factual judgment |
| `is_poisoned` | `true`; legacy construction marker |
| `injection_method` | `"type_preserving_hub_swap"` |
| `evidence` | Empty array; source QA does not support the injected claim |
| `injection_snapshots` | Synthetic overlay visibility inherited from the source edge |
| `observed_in_snapshots` | Compatibility field containing overlay snapshots; interpret using `snapshot_semantics` |
| `source_observed_snapshots` | Source-edge annotation observations |
| `snapshot_semantics` | Explicit explanation of the synthetic overlay boundary |
| `injection_provenance` | Source edge, same-type hub pair, pair permutation, swaps and derivation references |
| `factual_verification` | Separate factual status and evidence scope |

`injection_provenance.source_edge_index` is zero-based in the original edge array. `hub_pair` and `pair_permutation` describe one pair-local transposition; `swaps` identifies the changed endpoint positions. `source_question_ids` and `source_evidence_references` trace derivation only. The legacy `injection_provenance.factual_verification_status` remains `"unverified"`.

All 774 delivered synthetic edges have `factual_verification.status: "unresolved"`. The object also records `method`, local graph/QA matches, `evidence_refs`, `reason`, `relation_cardinality` and `temporal_scope`. Neither absence from the source graph nor an alternative object proves falsity.

## Questions and unresolved paths

Each question has `id`, `snapshot`, `split`, `projection_status` and `source_record`. Here `split` identifies `singlehop` or `multihop` annotation groups, not a training/test partition. `source_record` retains source fields such as the question, subject, text answers, answer annotations and relation path; fields can vary by source record.

An unresolved-path entry links a `question_id` and `snapshot` to a `reason` and any relevant diagnostics, such as `invalid_entities`. QA annotations and unresolved paths are not relabeled by injection.

## CSV tables and joins

CSV files have a header row. Parse integer labels explicitly; do not treat the strings `"0"` or `"False"` as Python booleans.

| File | Join key | Columns and interpretation |
|---|---|---|
| `original_KG/entity_id_value_type.csv` | `wikidata_id` = node `id` | `entity_value`, `value_status`, `entity_type`, `detailed_type_ids`, `labeling_method`, `type_policy_version`, `eligible_for_type_swap`, `data_quality_flags` |
| `edge_injection_labels.csv` | `edge_index` and directed triple | `edge_index`, `source`, `relation`, `target`, `is_synthetic_edge`, `synthetic_class`, `factual_verification_status` |
| `node_injection_labels.csv` | `qid` = node `id` | `qid`, `entity_type`, `is_synthetic_node`, `incident_to_synthetic_edge`, `synthetic_in_degree`, `synthetic_out_degree`, `synthetic_total_degree` |
| `hub_nodes.csv` | `qid` = node `id` | `qid`, `label`, `entity_type`, `in_degree`, `out_degree`, `total_degree`, `rank_within_type`, `selected_top_k`, `eligible_for_type_swap` |

`edge_index` is zero-based and valid only while graph edge ordering is preserved. Original rows have `is_synthetic_edge=0`, `synthetic_class=original`, and `factual_verification_status=not_adjudicated`. Injected rows have `1`, `fake`, and `unresolved`, respectively.

All node rows have `is_synthetic_node=0`. `incident_to_synthetic_edge=1` identifies any of the 654 existing entities participating in an injected edge. Synthetic total degree is synthetic in-degree plus out-degree.

Hub-table degrees are measured on the original graph. `selected_top_k` and `eligible_for_type_swap` use textual boolean values. The table covers eligible ranked entities, rather than every graph node; 206 rows are selected hubs.

## Snapshot visualization

Supported snapshots are `Dec2021`, `Dec2023`, and `March2024`. The adapter in [`display/snapshot_visibility.py`](display/snapshot_visibility.py) uses the following policy:

1. Include original nodes observed in the selected snapshot.
2. Add real nodes listed in `metadata.task1_hub_injection.injection_visibility[snapshot].synthetically_visible_nodes` as overlay activations.
3. Include original edges by `observed_in_snapshots` and synthetic edges by `injection_snapshots`.
4. Require both endpoints of every visible edge to be renderable.

The exported object has `snapshot`, `nodes`, `edges` and `legend`. Node wrappers contain `record`, `originally_observed`, `synthetically_activated` and `style_class`. Edge wrappers contain `record`, `synthetic` and `style_class`. Style classes are `observed-node`, `overlay-activated-node`, `observed-edge` and `synthetic-edge`.

The adapter does not mutate the source graph. An overlay activation changes display visibility only. Snapshot counts overlap and must not be summed to obtain unique graph totals. See the [display guide](display/README.md) for export commands.

## Manifests

- `injection_manifest.json`: generation configuration, input/source hashes, candidate diagnostics, budget and output hashes. The matching copy is in `hub_injection/outputs/`.
- `hub_injection/PORTABLE_MANIFEST.json`: pipeline file inventory and required original-input hashes. Its scope excludes `original_KG/`, which is included separately in this Git repository.
- `DELIVERY_MANIFEST.json`: repository file inventory, sizes and SHA-256 hashes. It excludes itself and generated local files.

Use `python tools/verify_repository.py` to validate the current repository layout. See [maintenance notes](docs/MAINTENANCE.md) before refreshing inventories or changing generation code.

# Knowledge Graph

**Group member:** Myeongchun Kim · Gahyeon Kim · Jiahang Li

A research dataset built from the [PAT-Questions](https://aclanthology.org/2024.findings-acl.777/) temporal question-answering annotations. It provides a directed, multi-relational knowledge graph (KG) with Wikidata-linked entities, typed relations, three annotation snapshots, and the original question-answer evidence. Alongside the original graph, this repository provides a **10% synthetically augmented KG** constructed through type-preserving hub-entity swapping, with explicit injection labels and provenance.

**QA snapshots:** `Dec2021` · `Dec2023` · `March2024`  
**Dataset format:** JSON + CSV · **Core tools:** Python 3.10+ (standard library; no API key or graph database required)

## Dataset overview

| Item | Count |
|---|---:|
| Entities (original and augmented) | 7,868 |
| Original relation triples | 7,737 |
| Synthetically injected triples | **774** |
| Augmented relation triples | **8,511** |
| Injection budget | **10% of original edges** (774 / 7,737) |
| Wikidata relation properties | 20 |
| General entity types | 35 |
| Original QA annotation records | 18,436 |
| Unresolved QA path projections | 496 |
| Selected hub entities | 206 |
| Existing entities incident to injected edges | 654 |
| Newly created synthetic entities | **0** |

The graph contains entities such as people, universities, cities, countries, organizations, and sports teams. Nodes retain their Wikidata QIDs, English labels, fine-grained `P31` classes, and general entity-type annotations. Directed edges retain Wikidata property IDs (for example, [`P54` — member of sports team](https://www.wikidata.org/wiki/Property:P54) and [`P69` — educated at](https://www.wikidata.org/wiki/Property:P69)), snapshot observations, and links back to the source QA records where available.

**Temporal interpretation:** A snapshot marks **observation in PAT QA annotations**, not the period in which a real-world fact was valid. The graph is a projection of QA paths, not a reconstruction of Wikidata's historical statement qualifiers.

## Construction and synthetic injection

The original graph is preserved in full. The injection procedure is **inspired by** [LogicPoison](https://aclanthology.org/2026.acl-long.252/), but uses *additive, pair-local hub swapping* rather than globally rewiring the original graph.

1. **Entity typing.** Map Wikidata `P31` (*instance of*) and available `P279` (*subclass of*) annotations to reviewed general types. Exclude entities flagged as unsuitable for swapping.
2. **Hub selection.** Group eligible entities by general `entity_type`, rank by original-graph total degree, and choose a Top-K set within each type.
3. **Candidate generation.** Swap compatible hub entities **of the same type** in existing directed triples, retaining relation roles and excluding existing, duplicate, or disallowed candidate triples.
4. **Additive injection.** Add 774 distinct synthetic triples to the original 7,737; do **not** remove original triples or create new entity nodes. The injection is deterministic under the recorded seed (`42`) and configuration.
5. **Provenance and validation.** Record each injected triple's originating edge, swapped hub pair, snapshot-overlay visibility, construction class, and separate factual-verification status.

```text
Original PAT-KG          7,868 nodes · 7,737 edges
         |
         v
Entity-type groups -> Top-K hubs -> compatible swap candidates
         |
         v
Add 774 synthetic relations (10% of original edge count)
         |
         v
Augmented PAT-KG         7,868 nodes · 8,511 edges
```

The injection label **`value: "fake"` means synthetically constructed**, **not independently verified as factually false**. All 774 injected claims currently have `factual_verification.status: "unresolved"`; none has been adjudicated as `verified_false` or `verified_true`. Missing from the original KG does not mean false, especially for multi-valued or time-dependent relations.

### Construction labels

| Record | Field | Interpretation |
|---|---|---|
| Injected edge (JSON) | `value: "fake"`, `edge_origin: "synthetic_injection"`, `is_poisoned: true` | Synthetic construction, not a factual truth judgment |
| Any edge (CSV) | `is_synthetic_edge` | `1` = injected; `0` = original |
| Any edge (CSV) | `factual_verification_status` | `unresolved` for injected; `not_adjudicated` for original |
| Any node (CSV) | `is_synthetic_node` | `0` for all nodes: no fictitious entities were created |
| Any node (CSV) | `incident_to_synthetic_edge` | `1` for an original entity participating in at least one injected edge |

Source QA evidence remains attached to **original** edges. For synthetic edges, `injection_provenance` traces how a candidate was constructed; the original question IDs are **derivation references**, not evidence that the injected claim is true.

## Quick start

Run these commands from the repository root with Python 3.10 or later. Core generation, tests, and snapshot export use the standard library and run offline.

**Export a snapshot for graph visualization:**

```sh
python display/export_snapshot.py \
  --graph pat_kg_poisoned_10pct.json \
  --snapshot Dec2023 \
  --output snapshot_Dec2023.json
```

The exported JSON wraps visible nodes and edges with display classes (original observation, synthetic overlay activation, and synthetic relation). The script produces **data for a renderer**, not an interactive website.

**Reproduce the 10% injection in a separate directory:**

```sh
python hub_injection/run_task1.py \
  --graph original_KG/pat_kg_merged.json \
  --entities original_KG/entity_id_value_type.csv \
  --work-dir regenerated \
  --injection-ratio 0.10 \
  --seed 42 \
  --top-k-max 20 \
  --hub-metric total_degree
```

This regenerates `regenerated/outputs/` and `regenerated/reports/` without modifying the original data. The initial Top-K maximum is a *soft* threshold: the implementation can expand its per-type candidate pools if needed. For full regeneration, environment-specific reproducibility details, and checksum validation, see the [reproduction guide](hub_injection/reports/REPRODUCTION_v2.md).

**Run the automated tests (macOS/Linux):**

```sh
PAT_KG_INPUT_DIR="$(pwd)/original_KG" python hub_injection/run_tests.py
```

**Run the automated tests (Windows PowerShell):**

```powershell
$env:PAT_KG_INPUT_DIR = (Resolve-Path .\original_KG).Path
python .\hub_injection\run_tests.py
```

The archived revised release reports **53/53 passing tests**. These tests check construction, data consistency, temporal overlays, and reproducibility; they are **not** a factual-truth or KGQA attack-success evaluation.

## Temporal snapshots

| QA observation snapshot | Visible nodes* | Visible relations | Injected relations |
|---|---:|---:|---:|
| Dec2021 | 6,784 | 7,053 | 642 |
| Dec2023 | 6,967 | 7,241 | 649 |
| March2024 | 7,090 | 7,011 | 609 |

\*Visible-node counts include a small **synthetic display overlay** (6, 1, and 4 real-node activations, respectively) so every displayed synthetic edge has renderable endpoints. These are not new entities and do not modify original QA observation lists. Relations can occur in multiple snapshots; snapshot counts must **not** be summed to obtain unique-edge totals. See [snapshot rules](SCHEMA.md#snapshot-visualization) and [`display/snapshot_visibility.py`](display/snapshot_visibility.py).

## File guide

| Path | Contents |
|---|---|
| [`original_KG/pat_kg_merged.json`](original_KG/pat_kg_merged.json) | Original entities, directed relations, QA annotations, and temporal observation metadata |
| [`original_KG/entity_id_value_type.csv`](original_KG/entity_id_value_type.csv) | Entity IDs and audited general entity types |
| [`pat_kg_poisoned_10pct.json`](pat_kg_poisoned_10pct.json) | Augmented KG; includes all original records plus 774 synthetic edges and their provenance |
| [`edge_injection_labels.csv`](edge_injection_labels.csv) | Edge construction labels for all 8,511 relations; indexed by zero-based `edge_index` |
| [`node_injection_labels.csv`](node_injection_labels.csv) | Node identity, injection participation, and synthetic in/out-degree features |
| [`hub_nodes.csv`](hub_nodes.csv) | Original-graph degree rankings, Top-K selection, entity types, and swapping eligibility |
| [`injection_manifest.json`](injection_manifest.json) | Injection parameters, hub selection, input hashes, and generation diagnostics |
| [`display/`](display/) | Non-mutating snapshot adapter and JSON export CLI |
| [`SCHEMA.md`](SCHEMA.md) | Field descriptions, label meanings, temporal and visualization semantics |
| [`hub_injection/`](hub_injection/) | Generation scripts, tests, analysis tools, and archived technical reports |
| [`hub_injection/reports/FINAL_REPORT_v2.md`](hub_injection/reports/FINAL_REPORT_v2.md) | Revision handoff, independent checks, and research limitations |
| [`hub_injection/reports/revision_audit/`](hub_injection/reports/revision_audit/) | Factual-status audit, structural diagnostics, figures, and validation artifacts |
| [`DELIVERY_MANIFEST.json`](DELIVERY_MANIFEST.json) | Minimal-package file sizes and SHA-256 checksums |

**Join conventions:** `nodes[].id` and the CSV `qid` identify the same Wikidata entity. `edges[].source`, `relation`, and `target` form a directed triple. `edge_injection_labels.csv` uses zero-based `edge_index`, which matches the current `edges` array **only while its ordering is preserved**. For graph counts, distinguish original-source `metadata.stats` from augmented `metadata.task1_hub_injection.augmented_statistics`.

## Validation and analysis

The release was checked for preserved original records, exact injection budget, valid node references, type-compatible substitutions, unique new triples, deterministic regeneration, and snapshot-display consistency. The revised delivery reports **53/53 automated tests passing** and review by four distinct OpenCode model families; the [technical report](hub_injection/reports/FINAL_REPORT_v2.md) documents review scope and limitations.

A structural diagnostic compares the hub-based injection with ten constrained random baselines. It evaluates degree, connectivity, common neighbors, components, and alternative paths. Some augmented-graph path measures are higher for hub-based injection, while original-graph structural evidence is mixed; paths may themselves traverse synthetic edges. **These results do not establish factual falsity or increased KGQA difficulty.** See [structural support analysis](hub_injection/reports/revision_audit/structural_support.md).

A bounded external Wikidata lookup covered 86 of 774 injected claims, without establishing any claim as true or false. The [factual-verification audit](hub_injection/reports/revision_audit/factual_verification_summary.md) documents the procedure and its limits. No GNN training, downstream KGQA accuracy measurement, or attack-success-rate experiment is included in this release.

## Usage notes

- **Observation is not validity.** QA snapshot membership does not prove that a Wikidata statement held at the corresponding calendar date.
- **Synthetic is not proven false.** `fake` and `is_synthetic_edge=1` describe how a triple was introduced; factual verification is recorded separately.
- **Entity participation is not entity fabrication.** All 7,868 entity QIDs refer to existing original nodes, including the 654 participating in synthetic relations.
- **QA annotations are unchanged.** Injected edges are not additions to the original question-answer ground truth, and this package does not define downstream train/test split or leakage-prevention protocols.
- **Incomplete knowledge is not contradictory knowledge.** Missing or alternative relation values should not automatically be treated as errors without relation-specific and time-specific evidence.

## Sources, attribution, and reuse

The original QA data and construction context are based on [PAT-Questions: A Self-Updating Benchmark for Present-Anchored Temporal Question-Answering](https://aclanthology.org/2024.findings-acl.777/). The injection design is informed by [LogicPoison: Logical Attacks on Graph Retrieval-Augmented Generation](https://aclanthology.org/2026.acl-long.252/), but the **additive, pair-local** graph transformation is this project's implementation choice. Item and property identifiers refer to [Wikidata](https://www.wikidata.org/).

This repository does not currently declare a project-wide dataset or code license. Check the terms of the upstream datasets and the permissions of the respective rights holders before redistribution or reuse; do not assume that linked sources grant unrestricted reuse.

# Structural support diagnostic

Computed from 7,868 original nodes, 7,737 original triples and 774 injected triples; 206 selected hubs. Completed random seeds: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9].

## Definitions and scope

Directed edge degree counts relation triples. Clustering, common neighbors, components and alternative paths use simple undirected projection; paths exclude the tested triple but preserve another parallel/reverse triple.

Alternative paths are measured in the completed augmented graph after removing the tested injected triple. They may use other synthetic triples. Original same-component and common-neighbor measurements use only original edges. Clustering assigns zero to degree below two. All original nodes, including isolates, enter global component counts.

## Controlled random comparison

Per injected source-edge provenance: exact relation/type/changed-position/source snapshot stratum; eligible original role-compatible donor, pair transposition, reject self/original/QA-positive/duplicate; random shuffled same power-of-two original replacement degree bin first, compatible random fallback if exhausted. Hub donors remain eligible. No global eligible pair enumeration.

The random diagnostic intentionally removes hub-ranked donor selection; it is a role-and-degree-bin-conditional comparison, not an exact null for the hub-ranked mechanism. Same source-edge and counterpart preserve source snapshot handling exactly; activation counts can differ because randomly replaced nodes have different original QA observations. Degree bins are [1], [2,3], [4,7], etc.; same bin does not mean equal degree. Endpoint degree means and fallback counts are reported. This is a conditional descriptive comparison, not a causal or fully degree-matched fairness claim.

| Metric | Hub | Random mean | Hub minus random | Seed SD | Random min/max |
|---|---:|---:|---:|---:|---|
| endpoint_original_degree_mean | 4.58204 | 4.40795 | 0.174096 | 0.013565 | [4.385658914728682, 4.427648578811369] |
| original_common_neighbor_mean | 0.00129199 | 0.00129199 | 0 | 0.00105491 | [0, 0.002583979328165375] |
| augmented_common_neighbor_mean | 0.0426357 | 0.0286822 | 0.0139535 | 0.00309359 | [0.025839793281653745, 0.03488372093023256] |
| original_same_component_fraction | 0.580103 | 0.582946 | -0.00284238 | 0.00742941 | [0.5736434108527132, 0.5956072351421189] |
| alternative_path_fraction | 0.998708 | 0.926873 | 0.0718346 | 0.00721152 | [0.9108527131782945, 0.9354005167958657] |
| component_count | 764 | 701.9 | 62.1 | 3.60401 | [695, 706] |

Intervals in JSON are approximate 95% Monte Carlo intervals for the random-baseline mean across completed seeds (normal approximation); they are not confidence intervals for graph sampling, factual falsity, downstream efficacy, or causal hub effects. Standardized differences use between-seed SD, not edge-level pooled effect sizes.

Degree-bin fallback edges by seed: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]. Exact degree-bin matched edges: [774, 774, 774, 774, 774, 774, 774, 774, 774, 774].

## Snapshot-aware effects

| Snapshot | Visible injected | Both originally observed | Synthetic node activations required | Active components |
|---|---:|---:|---:|---:|
| Dec2021 | 642 | 623 | 6 | 800 |
| Dec2023 | 649 | 643 | 1 | 813 |
| March2024 | 609 | 590 | 4 | 1070 |

Activation counts identify required overlay nodes, not invented historical observations. The consumer overlay adapter is validated separately. Per-seed snapshot counts, degrees, clustering distributions, components, pair/type/relation distributions and hashes are in structural_metrics.json.

Actual changed-position counts: {'source': 388, 'target': 386}. All 774 edges enter each random run; no subset is filtered. Two-position refusal is a future diagnostic boundary, not a current mismatch.

## Scientifically bounded interpretation

Observed endpoint original mean degree is 4.5820 versus random 4.4079, despite matched bins. Original common-neighbor mean is 0.001292 versus 0.001292; original same-component fraction is 0.5801 versus 0.5829. Thus the original-topology measures do not show a consistent general connectivity advantage.

After augmentation, alternative-path availability is 99.87% versus random mean 92.69%, and common-neighbor mean is 0.0426 versus 0.0287. These alternative paths may use other synthetic edges; the measures can reflect collective synthetic-edge concentration and cycles. Hub augmentation leaves 764 components versus random mean 701.9; more alternative paths therefore does not mean more global component merging.

Hub endpoint degree is an explicit selection characteristic. The table tests whether it co-occurs with untyped local/path connectivity under the documented conditional baseline. Mixed, weak, or reversed effects must remain visible; selecting high-degree endpoints alone does not establish stronger relation-specific support. Untyped paths and common neighbors do not verify a directed relation or factual claim. No GNN, LLM training, KGQA experiment, attack-success evaluation or factual truth inference was performed. These diagnostics cannot establish that synthetic injections make KGQA harder.

Reproduce: `python tools/analyze_structure_v2.py` from the project directory (or execute the script by absolute path). Standard library only; input paths and seed list can be overridden.

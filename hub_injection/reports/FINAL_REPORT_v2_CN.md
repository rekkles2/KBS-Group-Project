# Task 1 Revised Release v2 Handoff Report

## Changes and Independent Verification

Before revision, the complete previous version was independently backed up at `D:\学习\KBS_project\new_KG\releases\baseline_v1_20261016T103451+0900`. The original KG, CSV, and previous parent-directory ZIP were unchanged; the final root-level JSON is now an ordinary independent copy, without a Windows hard link.

Independent recomputation confirms 7,868 nodes, 7,737 original edges, 774 injected edges, 8,511 total edges, 18,436 QA, 496 unresolved paths, 206 hub nodes, and 9,853 unique candidates. Original entities, edges, QA, temporal observations, evidence, and metadata were fully preserved; previous injected triples and existing provenance were also unchanged. Additionally, node_injection_labels.csv contains 7868 rows and edge_injection_labels.csv contains 8511 rows: newly created synthetic entity identity and participation in injected relations are labeled separately; all entity identity labels are 0. The canonical generator adds value=fake to all 774 synthetic edges; zero real nodes or original edges are incorrectly labeled fake.

## Factual Verification

fake denotes only the synthetic class, not verified falsity. A separate factual_verification.status=unresolved was added, retaining legacy unverified. All 774 claims underwent exact positive matching against the original KG/PAT QA. Four successful Wikidata requests queried 40 subjects, covering 18 relations and 86/774 edges (11.1%); 688 had no external statement lookup. This purposive sample does not support population-level statistical inference. The cache preserves claims, qualifiers, references, URLs, timestamps, and hashes.

No identical current claim was found in the sample, but absence does not prove falsity; other objects of multivalued relations are not direct counterevidence, and current Wikidata cannot substitute for historical facts. The final result is **verified_false=0, verified_true=0, unresolved=774**; no verified misinformation subset is claimed. Models do not provide factual ground truth. The canonical offline workflow does not implicitly depend on network access or caches. Independent tampering tests reproduced a validation gap in which a fabricated verified_false label with a nonempty citation was accepted; the validator was repaired to reverify under the same explicit evidence context, with added regression tests.

## Snapshot Visibility

In the previous version, 38 distinct injected edges lacked original endpoint observations in at least one snapshot, comprising 19/6/19 edge-snapshot cases. The 642/649/609 visible injected-edge counts remain unchanged; a separate overlay activates 6/1/4 real QIDs, respectively, to make endpoints renderable. Original observation lists remain unchanged; no historical observations, validity intervals, or fake nodes are fabricated.

Actual CLI runs and automated tests of the three-snapshot adapter confirm zero non-renderable endpoints under the explicit overlay policy. Missing original observations remain preserved; the overlay must not be treated as historical evidence. Snapshot counts overlap and must not be summed as unique edges. The previous HTML explorer contains only the original graph, with no claim of synthetic styling support; this release provides a documented adapter.

## Type-Preserving Swapping and Structural Support

The original configuration is retained: ratio=.10, seed42, initial topK20, original-graph total_degree ranking, and pair-local transposition; both endpoints use the same pair mapping for each candidate, while different candidates may use overlapping pairs. **Pair-local additive graph injection != global graph rewiring**. Exact LogicPoison reproduction is not required; no Task 2, training, or KGQA efficacy experiments are performed.

All 10 random seeds generated 774 legal baseline edges, matched by source edge, type, relation, replacement position, snapshot, and original degree bin. No fallback occurred, but degrees still differ within bins (endpoint means 4.58204/4.40795); exact matching or causal fairness is not claimed. Actual changes are source-only388, target-only386, and both-endpoints0; all 774 edges enter every structural comparison.

Original-graph common-neighbor means are both .001292, with same-component proportions .58010/.58295; original structural support is not uniformly stronger. After augmentation and exclusion of the tested edge, alternative-path proportions are .998708/.926873, and paths may use other synthetic edges; common-neighbor means are .042636/.028682. The hub graph retains 764 components versus a random mean of 701.9 (originally 808), while clustering averaged over all nodes decreases. All mixed and opposite-direction results are retained. These metrics use a simple undirected projection and cannot verify directed relations, facts, or attack efficacy; intervals describe only Monte Carlo variation of ten random-baseline means.

## Figures, Reproducibility, and Regression Tests

Both SVGs were actually rendered, and before/after PNGs were inspected; the 18 relation categories and 23 type categories each total 774. Counts, widths, and text boundaries were checked bar by bar. Captions distinguish synthetic construction from factual truth. The complete regression suite **passed 53/53**. An independent copy of code and real inputs generated outputs twice from nonexistent output directories; all six file hashes matched delivery, and the copied full test suite also passed. Integration tests additionally ran seed42/42/43.

The verified environment is Python3.10.0 plus the standard library; the browser was used only for figure audits. The portable ZIP excludes original data, provides a filename/size/SHA-256 manifest and explicit-path commands, and does not depend on API keys, caches, or hard links. Byte-identical shuffling across Python versions is not promised. See REPRODUCTION_v2_CN.md for detailed steps.

## Adversarial Review

Actual models/families: deepseek-v4-pro, glm-5.3, qwen3.8-max, gemini-4-argon-contributor; substantive rounds: 4; consensus: YES. Initial independent opinions, cross-examination, failed responses, usage, and adjudication are preserved. Gemini actually received two PNGs; text models were not described as having viewed images or executed code. After default thinking caused insufficient response text or timeouts, model-specific parameters were adjusted according to primary-source documentation; no other paid provider was used and no credentials were copied.

Source hashing was expanded to tools/tests/configuration; an executed counterexample refuted the claim that sorting before shuffling is unnecessary. The 388/386/0 distribution clarified the structural baseline scope; the client date 2026-10-16 refuted the alleged October anomaly. All original opinions, incorrect conjectures, and remaining minor suggestions are preserved in findings_registry.json and final_adjudication.md; factual uncertainty was not concealed by majority voting.

## Files and Evidence

Final KG: ../pat_kg_poisoned_10pct.json; canonical data: JSON, JSONL, manifest, and hub CSV under outputs/. Code/tests: src/, tests/, tools/. Audits: baseline hashes, independent counts, factual CSV and cache, structural diagnostics, before/after figure screenshots, snapshot CLI, and portable reproduction evidence under revision_audit/. Review: multi_model_review/. Logs: tests.log, validation_results.json, final_verification.json. Bilingual reproduction instructions and CHANGELOG_v2.md are also included. Previous reports remain in an independent backup.

Input graph SHA-256: `f5a1c2f4b556bf060e89540ab1b5c05f836afe29cc0f13cdcd80f92120171f31`; CSV: `c653dde9d87f61295dac67aac1151d5510c7d6b9c0081ada82b31ea1f053be2e`; final graph: `9860778471610593bf45d97096002abe321cb6417f583a41108408c26b092fcf`.

```text
TASK 1 REVISED STATUS: PASS
Original nodes preserved: YES
Original edges preserved: YES
Injected edge count: 774
Total edge count: 8511
Injected edges labeled value=fake: 774
Original nodes incorrectly labeled fake: 0
Verified false statements: 0
Verified true statements: 0
Unresolved factual statuses: 774
Snapshot visibility violations: 0 under explicit overlay adapter
Structural-support analysis completed: YES
Visualization review completed: YES
Automated tests passed: 53 / 53
Distinct OpenCode model families used: 4
Adversarial review rounds: 4
Multi-model consensus: YES
Remaining blocking issues: none supported within revised Task 1 scope
Remaining methodological limitations: 774 factual claims unresolved; purposive external coverage 86/774; undirected structural proxies; conditional degree-bin baseline; offline merged snapshots; no downstream efficacy evaluation.
```

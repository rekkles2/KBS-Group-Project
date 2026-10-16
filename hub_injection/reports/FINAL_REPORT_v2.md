# Task 1 revised release v2

## Executive result and preserved baseline

The existing implementation was revised in place after an independent byte-copy backup at `D:\学习\KBS_project\new_KG\releases\baseline_v1_20261016T103451+0900`. Original input files and the prior parent ZIP were preserved. The final graph at `../pat_kg_poisoned_10pct.json` is an ordinary independent copy matching outputs; no Windows hard link is needed.

Independent recomputation confirms 7,868 nodes, 7,737 original edges, 774 additions, 8,511 total edges, 18,436 QA, 496 unresolved paths, 206 selected hubs and 9,853 eligible unique candidates. Every original object, edge ordering, QA/evidence/temporal assignment and source metadata remains unchanged. Every pre-existing injected triple and provenance field also remains identical. Input hashes are in revision_audit/original_file_hashes.json; independent hub ranking and all-pair candidate counts are independently recorded.

## Synthetic annotation and factual verification

All 774 synthetic edges now carry `value: "fake"`; no original edge or real Wikidata node is relabeled. fake denotes synthetic construction, **not proven factual falsity**. Separate factual_verification.status is unresolved; legacy provenance unverified is retained unchanged. The canonical pipeline generates the labels and the validator checks serialized output.

All 774 exact claims were compared with original KG/PAT positive annotations, finding no identical positive. Four actual HTTP-200 Wikidata requests retrieved 40 subjects, covering all 18 relations and 86/774 claims (11.1%). The purposive sample is not statistical coverage; 688 claims have no external statement lookup. Raw statements, qualifiers, references, URLs, timestamps and hashes are cached. No identical current claim was found in that sample. Missing or different objects are not falsity proofs, especially for multivalued/time-dependent relations. Current statements cannot establish historical snapshot truth. Result: **0 verified_false, 0 verified_true, 774 unresolved**. No verified misinformation subset or unsupported replacement is claimed.

Canonical generation remains offline and deterministic. The factual-layer API supports explicit reviewed evidence; its legacy fields remain immutable. An executed tampering test demonstrated that a bogus verified_false label with a nonempty citation was previously accepted. The validator now rederives annotations under the same explicit evidence context and rejects that mutation. Model assessments never supply factual ground truth.

## Snapshot visibility repair

Baseline audit confirmed 38 distinct injected edges with an originally unobserved endpoint in at least one snapshot: 19/6/19 edge-snapshot cases for Dec2021/Dec2023/March2024. Visible injected-edge counts remain 642/649/609. Added namespaced overlay lists activate 6/1/4 real QIDs, respectively. Original observed_in_snapshots arrays are unchanged. Synthetic activation is not an invented original observation, fake node or historical validity interval.

The non-mutating snapshot adapter distinguishes original observation, real-node overlay activation and synthetic edge styling. All three actual CLI exports and automated tests have zero non-renderable visible endpoints under that explicit policy. The original-observation mismatch is deliberately retained, not reinterpreted as repaired historical evidence. Per-snapshot counts overlap and must not be summed as distinct graph edges.

## Pair-local method and structural support

Configuration and pair-local method were retained: ratio .10, seed42, initial topK20, original total-degree ranking, same-type eligible donors and directed relation-role evidence. Both positions use a fixed pair's transposition; different candidates may use overlapping pairs. **Pair-local additive graph injection != global graph rewiring**. This is not exact LogicPoison reproduction. No Task 2, training or KGQA efficacy experiment was run.

Ten random seeds each generated 774 legal diagnostic edges matching source edge, type, relation, changed position and snapshots. Replacement original-degree bins all matched without fallback, but exact degree did not: endpoint means Hub 4.58204 versus random 4.40795. Actual changes are source-only388, target-only386, two-position0; all 774 entered each baseline, with no hidden filtering.

Clustering/common-neighbor/component/path metrics use an explicitly simple undirected projection and do not verify a directed relation. Original common-neighbor means are both .001292; original same-component proportions .58010 versus .58295, so original-topology support is not uniformly stronger. Augmented alternative-path proportions are .998708 versus .926873 after excluding the tested triple, but paths may use other synthetic edges. Augmented common-neighbor means .042636 versus .028682. Hub leaves764 components versus random701.9 (808 originally); average global local clustering decreases. These are mixed descriptive results, not causal hub advantages or attack success. Reported intervals concern Monte Carlo variation of ten random-baseline means, not factual confidence or downstream effects.

## Figures and standalone reproducibility

Both delivered SVGs were actually rendered and viewed before/after. Eighteen relation and23 type categories independently total774; every count, bar width and text boundary was checked. Captions now distinguish synthetic injection from verified falsity. The parent HTML explorer embeds only the original graph; no synthetic styling is claimed for it. The documented adapter is the v2 consumer interface.

Final suite: **53/53 passed**, no failures/errors/skips. An isolated independent copy of code and actual supplied inputs regenerated from absent output directories twice; all six output files match delivery, and the copied full suite passed. Separate integration tests run seeds42,42,43 under python -E -S. Python3.10.0/stdlib is the verified generation environment; browser tooling is optional for figure audits. Exact cross-version shuffle bytes are not promised. Portable ZIP omits original datasets with complete filename/size/SHA-256 input manifest; explicit input paths require no hardlink, API key or stale cache. See REPRODUCTION_v2.md and REPRODUCTION_v2_CN.md.

## Adversarial multi-model review

Models/families: deepseek-v4-pro, glm-5.3, qwen3.8-max, gemini-4-argon-contributor. Substantive rounds: 4; consensus: YES. Actual requests, responses, IDs, timestamps, usage and failures are preserved. Gemini received actual PNG bytes through the documented OpenCode Go Google route after chat-protocol rejection. Other initial requests exhausted reasoning or timed out; model-specific controls were checked in primary documentation and used in recorded retries. No provider fallback or key copying occurred. Text reviewers never claimed local execution or image inspection.

Findings were reconciled with actual code and counterexamples. Source hashes now cover runtime, tests, tools, entry scripts, configuration and requirements. Removing pre-shuffle sorting was rejected by an executed input-order counterexample. A supposed two-position diagnostic mismatch was rejected by the actual388/386/0 distribution. The alleged anomalous October date was rejected against the client date2026-10-16. All reviewer findings, including false positives and editorial limitations, remain in findings_registry.json and final_adjudication.md. External facts were not decided by vote.

## Reproduction, inventory and limitations

Core outputs: outputs/pat_kg_poisoned_10pct.json, injected_edges.jsonl, injection_manifest.json, hub_nodes.csv, node_injection_labels.csv, edge_injection_labels.csv. The node CSV separately records original-vs-synthetic entity identity and participation in synthetic relations; all node identity targets are0. The edge CSV provides binary construction labels for all8511 directed triples. Code/tests/config: src/, tests/, tools/, run_task1.py, run_tests.py. Reports: revision_audit/ (baseline, independent reconciliation/candidate count, factual CSV/cache, structural metrics, actual renders/visual audits, snapshot CLI, portable reproduction), multi_model_review/, tests.log, validation_results.json, final_verification.json, bilingual reproduction and CHANGELOG_v2.md. The original v1 report remains in the independent backup.

Input graph SHA-256 `f5a1c2f4b556bf060e89540ab1b5c05f836afe29cc0f13cdcd80f92120171f31`; CSV `c653dde9d87f61295dac67aac1151d5510c7d6b9c0081ada82b31ea1f053be2e`. Final graph SHA-256 `9860778471610593bf45d97096002abe321cb6417f583a41108408c26b092fcf`. All unresolved claims and methodological limits are explicit above. Main steps: run_task1.py with --graph/--entities; run_tests.py with PAT_KG_INPUT_DIR; audit_facts_v2.py; analyze_structure_v2.py; package_release_v2.py --check-clean; verify_delivery.py; build_handoff_v2.py. Exact commands and package extraction are in the bilingual reproduction documents.

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

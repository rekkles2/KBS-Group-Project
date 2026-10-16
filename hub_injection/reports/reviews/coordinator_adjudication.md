# Coordinator review adjudication

All raw API outputs and prompts are preserved. Reviewer output is advisory, not proof that local code ran. Reviewers A, B and C were independent text-only OpenCode `kimi-k2.6` requests; A and C also received a separate follow-up with exact scope, counterexamples and the updated code/tests.

## Substantive OpenCode implementation contribution

`implementation_retry_response.json` contains the generated incidence-indexed pairwise candidate enumerator, original role-signature constraints, deterministic traversal and rejection accounting. The first implementation attempt returned no usable final text; its error is preserved. The successful retry returned `ok=true`, `finish_reason=stop` and usage. The returned code assumed attribute-access objects; the coordinator adapted it to the actual JSON dictionary schema and added original-reference, strict-eligibility, duplicate-hub and isolated-hub guards. The contributed algorithm remains identifiable in `src/generate_candidates.py` and is checked by local tests and an independent validator.

## Decisions on initial review findings

| Finding | Decision | Evidence / action |
|---|---|---|
| Overlay must use disjoint hub pairs or one global bijection | Not a requirement of this additive candidate-pair adaptation; retain explicit method limitation | For each fixed pair, both endpoint positions use its same transposition. Different candidates may use overlapping pairs. The overlay is a union of candidate-specific perturbations and is never described as a global permutation. A's follow-up accepts this boundary. |
| Prefix expansion can exceed eligible count | Rejected | `min(len(group), ...)` bounds the prefix. The tiny graph test reaches all three eligible nodes and stops. The initial top-K cap is intentionally soft during expansion, as documented. No expansion occurs on the real data. |
| Missing source-edge-index sort key causes nondeterminism | Rejected | Accepted triples are already unique before sorting, so their first three sort fields cannot tie. Pair and incident-index traversal are sorted. Independent-process byte comparisons pass. |
| Original-triple exclusion is absent in validator | Already implied by original-prefix preservation plus unique augmented triples; add direct check for clarity | `no_original_triples` is now an explicit additional check. A's follow-up still overlooked that exact check despite its presence in the supplied code; the coordinator verified it directly. |
| Second validation overwrites an earlier failure | Rejected | Each failed check raises immediately. Both passes execute. Added direct equality between generated and reloaded JSON graph for a clearer round-trip guarantee. |
| Manifest is written before serialized validation | Rejected | Actual runner writes the manifest after reloaded-object validation and input hash checks. Initial review cited guessed line order. |
| Small buckets can starve the dominant type and underfill | Rejected; add adversarial tests | Every nonempty bucket can make progress. Tests sample all 40 candidates with a one-element type and exhaust an oversized request without fabrication. |
| Missing shortfall/expansion integration test | Accepted coverage gap and fixed | Tiny three-node directed cycle requests 30 additions, expands K from 2 to 3, emits only the complete three-edge complement and records PARTIAL. |
| Same-seed comparison omits deterministic reports | Accepted coverage improvement and fixed | Reproducibility test now compares every generated report as well as all four output files across two seed-42 CLI runs. |
| Reuse cached generator evidence in validator | Declined | Rebuilding role signatures from the original graph gives an independent check and is fast enough on this dataset. |
| Exact synthetic edge-field validation limits future extension | Intentional current schema discipline | The strict allowlist prevents silently added validity qualifiers; schema changes must deliberately update validation and tests. |
| Balanced does not mean equal marginal counts | Retained and documented | Sampling is round-robin by type then relation; sparse candidate buckets limit equalization. Actual distributions are reported. |
| General types and role evidence cannot verify facts | Retained limitation | No injected triple is labeled false; all 774 are unverified. No historical validity intervals or attack-effectiveness conclusions are produced. |

Final external dispositions: A follow-up **PASS**, B **APPROVED_WITH_MINOR_FINDINGS**, C follow-up **ACCEPT**. These verdicts do not replace local verification. The delivered real-data graph passes 27 invariant categories (applied over every synthetic edge), and the final suite passes 28/28 tests with no skips. No unresolved supported blocking defect remains within Task 1 scope.

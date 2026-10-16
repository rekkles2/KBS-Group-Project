# Reports and evidence index

Use the [repository README](../../README.md) for current checkout commands and the [data reference](../../SCHEMA.md) for field semantics. Reports below retain the paths, execution environment and claims recorded at the time of the v2 release.

| Start here | Purpose |
|---|---|
| [FINAL_REPORT_v2.md](FINAL_REPORT_v2.md) | Revised release results, checks and research limitations |
| [REPRODUCTION_v2.md](REPRODUCTION_v2.md) | Historical portable-ZIP reproduction protocol and input hashes |
| [CHANGELOG_v2.md](CHANGELOG_v2.md) | Changes made during the v2 revision |
| [validation_results.json](validation_results.json) | Serialized graph validation |
| [tests_summary.json](tests_summary.json) | Archived 53-test execution summary |
| [final_verification.json](final_verification.json) | Archived delivery checks |

## Audits and diagnostics

| Evidence | Purpose |
|---|---|
| [01_original_dataset_audit.md](01_original_dataset_audit.md) | Input checks and annotation semantics |
| [02_hub_selection.md](02_hub_selection.md) | Hub ranking and selection |
| [03_injection_statistics.md](03_injection_statistics.md) | Injection counts and distributions |
| [04_validation_results.md](04_validation_results.md) | Construction validation |
| [05_limitations.md](05_limitations.md) | Original analysis boundaries |
| [Factual verification](revision_audit/factual_verification_summary.md) | 774 local audits, bounded external lookup and unresolved status |
| [Structural support](revision_audit/structural_support.md) | Ten-seed constrained random comparison and mixed structural results |
| [Visual review](revision_audit/visual_review.md) | Chart arithmetic, geometry and archived render checks |
| [Portable reproduction](revision_audit/portable_reproduction.json) | Historical clean-copy execution evidence |
| [Sources and boundaries](sources_and_boundaries.md) | Source attribution and methodological scope |

## Historical material

`FINAL_REPORT.md`, `reviews/` and the baseline audit files record earlier implementation and review stages. `multi_model_review/` contains archived model responses, adjudication and execution logs. These are supplementary process evidence, not factual ground truth or a substitute for tests.

Files with `_CN` suffixes are retained under their historical names. The delivered `REPRODUCTION_v2_CN.md` duplicates the English guide, and `FINAL_REPORT_v2_CN.md` is also written in English; the filenames do not establish that Chinese translations are available.

Historical absolute paths and references to parent releases or an explorer describe the original working environment. Those files are not required to use this checkout. Do not run handoff/review builders merely to refresh documentation: some overwrite reports or invoke external providers. See [maintenance notes](../../docs/MAINTENANCE.md).

# Repository maintenance

## Layout and authoritative copies

The repository root provides the augmented graph and label tables for downstream use. `original_KG/` holds the unchanged generation inputs. `hub_injection/outputs/` retains pipeline copies of the root delivery files plus `injected_edges.jsonl`. Keep both copies: historical tooling and output hashes refer to the pipeline paths.

`hub_injection/reports/` retains release evidence. Its [index](../hub_injection/reports/README.md) separates the revised report from earlier records. Historical machine paths are provenance, not installation requirements. The Git repository name `KBS-Group-poroject` is retained so existing clone URLs and links continue to work.

## Local verification

From the repository root:

```sh
python tools/verify_repository.py
```

This offline check validates both file inventories, generation input/source/output hashes, duplicate delivery copies, graph preservation, label alignment, snapshot counts, Python syntax and relative Markdown file links. It does not run the automated test suite or query external evidence. It exits nonzero on failure and prints a JSON result.

Run all existing tests separately. PowerShell:

```powershell
$env:PAT_KG_INPUT_DIR = (Resolve-Path ./original_KG).Path
python -m unittest discover -s hub_injection/tests -t hub_injection -v
```

POSIX shell:

```sh
PAT_KG_INPUT_DIR="$PWD/original_KG" python -m unittest discover -s hub_injection/tests -t hub_injection -v
```

Direct `unittest` invocation preserves the archived test reports. The existing `hub_injection/run_tests.py` runner is also supported with the same environment variable, but replaces `hub_injection/reports/tests.log` and `tests_summary.json`.

## Reproduction and checksums

Generate into `regenerated/` using the command in the [README](../README.md#quick-start). Do not overwrite delivered outputs during a documentation pass. The existing pipeline's default input locations refer to the original parent workspace; always pass `--graph` and `--entities` explicitly in this checkout.

The injection manifest hashes generation source, tests, tools and configuration. Changing those files intentionally affects regenerated metadata and output hashes. Documentation and the root maintenance verifier are outside that generation-source hash set. `.gitattributes` preserves delivered bytes across clones, including existing line endings.

After intentional documentation changes, refresh the two inventory manifests:

```sh
python tools/verify_repository.py --refresh-manifests
```

Refresh validates the graph, generation hashes and links before writing inventories, then checks the updated inventories. It does not regenerate the graph, change the injection manifest or run tests. Inventory refresh is not evidence that modified experiments are valid. Commit the updated inventories together with the documented changes.

## Optional and historical tools

| Tool | Scope |
|---|---|
| `display/export_snapshot.py` | Current root-level snapshot export |
| `hub_injection/tools/export_snapshot_v2.py` | Pipeline snapshot export with explicit graph/output arguments |
| `hub_injection/tools/package_release_v2.py` | Portable packaging and clean-copy verification; pass both input paths |
| `hub_injection/tools/analyze_structure_v2.py` | Optional structural diagnostics; pass `--original original_KG/pat_kg_merged.json` from the repository root |
| `hub_injection/tools/audit_facts_v2.py` | Optional cached factual audit; pass `--original original_KG/pat_kg_merged.json`; `--fetch` refreshes external evidence |
| `hub_injection/tools/verify_delivery.py` | Archived verifier for the old parent-workspace layout; use the root verifier for this checkout |
| Handoff, review and model-discovery tools | Historical release/review automation; may overwrite reports or require provider access |

Generation, tests, export and repository verification need only Python 3.10+ and the standard library. Optional browser screenshot tools need their separately configured browser runtime. External review calls are not required for reproduction.

## Data interpretation and reuse

Keep synthetic construction labels separate from factual truth. Keep annotation observations separate from validity intervals. Avoid using provenance or injection-label fields as prediction features when evaluating detection models; define splits and leakage controls before any downstream experiment.

The repository includes an [MIT License](../LICENSE). Preserve its notice for covered code. PAT-Questions annotations and Wikidata-derived content retain their applicable upstream terms; the repository license does not replace third-party rights or licensing requirements.

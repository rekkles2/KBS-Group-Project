# Task 1 v2 reproduction

The portable ZIP contains generation code, tests, configuration, diagnostics, outputs, reports and visual evidence. Original input datasets are supplied separately; they are not optional. No credentials or OpenCode access are required to regenerate or validate the graph. API review reproduction is a separate activity and requires authorized provider access.

## Required inputs

| CLI argument | Filename | Bytes | SHA-256 |
|---|---|---:|---|
| `--graph` | `pat_kg_merged.json` | 40683218 | `f5a1c2f4b556bf060e89540ab1b5c05f836afe29cc0f13cdcd80f92120171f31` |
| `--entities` | `entity_id_value_type.csv` | 702640 | `c653dde9d87f61295dac67aac1151d5510c7d6b9c0081ada82b31ea1f053be2e` |

The ZIP's `PORTABLE_MANIFEST.json` records every packaged member's size/hash, input requirements and exclusions. Verify the original datasets against these hashes before running.

## Generate and test

Use Python 3.10 or later. Runtime and graph tests use only the Python standard library; `requirements.txt` records this. The execution audited here used CPython 3.10.0 on Windows. Extract the ZIP to an arbitrary directory, open a terminal in `task1_hub_injection`, and provide actual input paths explicitly:

```powershell
python run_task1.py --graph 'C:\input\pat_kg_merged.json' --entities 'C:\input\entity_id_value_type.csv' --work-dir '.\regenerated' --seed 42 --injection-ratio 0.10 --top-k-max 20
$env:PAT_KG_INPUT_DIR = 'C:\input'
python run_tests.py
```

On POSIX shells, use equivalent paths and `PAT_KG_INPUT_DIR=/input python run_tests.py`. Output files are regenerated in `regenerated/outputs`; reports are in `regenerated/reports`. The initial `top_k_max=20` is a soft prefix limit; the documented expansion policy may exceed it. The configuration JSON is documentation of defaults, not an automatically loaded CLI config file. There is no dependency on a Windows hard link, previous output graph or cached API response.

Compare SHA-256 values of regenerated `pat_kg_poisoned_10pct.json`, `injected_edges.jsonl`, `injection_manifest.json` and `hub_nodes.csv` with the delivered `outputs/` files. A changed generation source hash intentionally changes the manifest and graph metadata, so compare against outputs regenerated from the same source revision.

## Clean-copy verification

```powershell
python tools/package_release_v2.py --graph 'C:\input\pat_kg_merged.json' --entities 'C:\input\entity_id_value_type.csv' --check-clean reports/revision_audit/portable_reproduction.json
```

This copies source/tests and original inputs into a fresh temporary location, deliberately omits output/cache directories, runs generation twice with seed 42, compares all output bytes with each other and the release, and executes the copied test suite with the explicitly supplied input directory. Actual results and stdout/stderr are recorded in `revision_audit/portable_reproduction.json`. This verifies path independence in the current interpreter/environment; it is not proof of successful execution on a separate operating system or an independently installed Python version. Cross-version floating-point rendering and runtime differences are not asserted byte-identical.

## Rebuild the portable ZIP

```powershell
python tools/package_release_v2.py --graph 'C:\input\pat_kg_merged.json' --entities 'C:\input\entity_id_value_type.csv' --destination 'C:\release\task1_v2_portable.zip'
```

The destination must not already exist. The package deliberately excludes credential filenames, `.opencode-local`, Git internals, `__pycache__`, dependency folders, previous ZIPs and baseline releases. Originals remain separate. The ZIP archive byte hash can differ because archive timestamps are not normalized; member hashes establish content integrity.

## Figures and snapshot visibility

Chart arithmetic and SVG widths can be independently checked without external packages:

```powershell
python tools/audit_visuals_v2.py --graph regenerated/outputs/pat_kg_poisoned_10pct.json --reports regenerated/reports --json reports/revision_audit/visual_counts_after.json
```

Actual browser screenshots in `output/playwright/before/` and `after/` were rendered using installed Node.js Playwright and Chromium. Rendering is optional and requires supplying `--screenshots`, `--playwright-module` and, when browser versions differ, `--chromium`. No browser installation is performed by the script. These optional visualization tools are not graph-runtime dependencies.

Use `tools/export_snapshot_v2.py --help` for the synthetic visibility adapter. The parent project's `PAT_Temporal_KG_Explorer.html` is an original-data explorer outside this release. Its node filtering and edge styling do not consume the new synthetic overlay, so importing the revised graph there is not a supported validation of synthetic styling. The adapter documents the supported graph-consumer boundary; no synthetic browser explorer is delivered.

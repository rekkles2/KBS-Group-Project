# Snapshot export

Run from the repository root with Python 3.10 or later:

```sh
python display/export_snapshot.py --graph pat_kg_poisoned_10pct.json --snapshot Dec2023 --output snapshot_Dec2023.json
```

This single-line command also works in PowerShell. Choose `Dec2021`, `Dec2023`, or `March2024`. To export original observations only, pass `--graph original_KG/pat_kg_merged.json`.

The output is JSON for a renderer. This directory contains the export CLI and a non-mutating visibility adapter; it does not contain an interactive web application. See [snapshot semantics and wrapper fields](../SCHEMA.md#snapshot-visualization).

| Snapshot | Visible nodes | Visible edges | Synthetic edges | Real nodes activated by overlay |
|---|---:|---:|---:|---:|
| Dec2021 | 6,784 | 7,053 | 642 | 6 |
| Dec2023 | 6,967 | 7,241 | 649 | 1 |
| March2024 | 7,090 | 7,011 | 609 | 4 |

Preserve the distinction between `observed-node`, `overlay-activated-node`, `observed-edge` and `synthetic-edge` when rendering. The `fake` class describes construction; it is not a verified factual-falsity label.

`hub_injection/src/snapshot_visibility.py` is the pipeline's matching adapter. The repository verifier checks that the two adapters remain byte-identical.

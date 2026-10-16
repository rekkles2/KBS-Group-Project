# Delivered visualization review

## Inventory and actual image inspection

The release inventory contains two source figures: `reports/injected_by_relation.svg` and `reports/injected_by_type.svg`. No additional JPG, PDF, GIF or scientific plot was found in the release. Timestamped baseline releases are backups, not additional figures. This audit adds four actual Chromium-rendered PNG evidence images:

- `output/playwright/before/injected_by_relation.png`
- `output/playwright/before/injected_by_type.png`
- `output/playwright/after/injected_by_relation.png`
- `output/playwright/after/injected_by_type.png`

Both before and both after images were opened with the image-viewing tool and visually inspected. The baseline SVG files were read from `releases/baseline_v1_20261016T103451+0900`; the after images use the regenerated current SVGs. Screenshots use actual SVG element bounds at device scale 1. No model was credited with inspecting image pixels merely from source code.

## Numerical audit

`tools/audit_visuals_v2.py` independently loads the baseline/revised graph and identifies injected edges by `is_poisoned is True`, without trusting precomputed statistics JSON. For each figure it recomputes category counts, parses every displayed SVG category/value, and checks every bar width against `540 * count / max_count`, to the SVG's two-decimal rounding tolerance of 0.00501 pixels. It checks count-label placement and verifies room within the canvas.

| Figure | Categories | Sum | Count errors | Bar-width errors | Clipped text boxes |
|---|---:|---:|---:|---:|---:|
| Relation, before | 18 | 774 | 0 | 0 | 0 |
| Entity type, before | 23 | 774 | 0 | 0 | 0 |
| Relation, after | 18 | 774 | 0 | 0 | 0 |
| Entity type, after | 23 | 774 | 0 | 0 | 0 |

Relations: P102=33, P108=60, P112=69, P115=57, P127=19, P1365=32, P159=59, P169=14, P19=41, P26=8, P27=30, P286=9, P35=2, P39=32, P488=129, P54=9, P6=61, P69=110.

Entity-type counts, full category lists and browser `getBBox()` values are recorded in `visual_counts_before.json` and `visual_counts_after.json`. The relation figure is 920 × 604 pixels; the entity-type figure is 920 × 744 pixels. There are no percentages or numerical axes to misstate. Bars share a zero baseline and each category has a direct integer label; independent scaling is per figure. No cross-figure bar-width comparison is implied.

## Visual findings and repair

All text remains readable at native size, including the longest `HigherEducationInstitution` label. Category labels, bars and integer labels do not overlap. Browser text bounding boxes remain inside the SVG canvas in both versions. Rows use consistent 28-pixel spacing, 20-pixel bars, sans-serif text, white background and one dark-blue color (`#245c91`). The dark blue has approximately 7:1 contrast against white; text is black. A single series needs no color legend. QID-style property labels retain exact Wikidata property IDs, avoiding invented relation names. The SVG `role=img` and `aria-label` provide a title, but a complete screen-reader data table is not embedded; the machine-readable statistics and audit JSON supply exact values.

The confirmed documentation issue was a subtitle that referred to seed 42 by default and did not explicitly distinguish synthetic injection from factual falsity. The generator now uses: `Synthetic injection counts; not verified factual falsity. Unique triples.` Regenerated SVGs and actual after screenshots show this text. Counts and geometry are unchanged. No figure claims all 774 synthetic edges are proven false. The figures are suitable for a technical report; a formal publication may choose expanded property names and a typeset caption without altering the audited counts.

## Graph explorer and supported consumer boundary

The parent project's `PAT_Temporal_KG_Explorer.html` was inspected read-only; it is outside the revised Task 1 release. Its embedded gzip/base64 JSON was decoded independently and contains 7,868 nodes, 7,737 edges and 0 synthetic edges. At source line 98 `snapHas()` reads only `observed_in_snapshots`; line 109 filters nodes before edges; line 115 `visEdge()` does not read `value: fake`, `edge_origin` or overlay metadata. Consequently it does not implement the revised synthetic styling/visibility policy. No claim is made that fake-edge styling, browser snapshot transitions or synthetic ego-graphs were visually tested in that original-data explorer. No replacement explorer is delivered.

The release instead supplies `src/snapshot_visibility.py` and `tools/export_snapshot_v2.py` as the documented consumer adapter. Its output contains node/edge wrappers with source `record` preserved, explicit `style_class`, original observation versus synthetic activation flags, and a legend separating synthetic class from factual truth. This is an exported view schema for a consumer to render; it is not a rendered interactive UI.

All three snapshot CLI exports were actually executed into a fresh temporary directory and independently reloaded. `snapshot_adapter_independent.json` records:

| Snapshot | Renderable nodes | Renderable edges | Synthetic edges | Overlay activated real nodes | Dangling edges | Nodes labeled fake |
|---|---:|---:|---:|---:|---:|---:|
| Dec2021 | 6784 | 7053 | 642 | 6 | 0 | 0 |
| Dec2023 | 6967 | 7241 | 649 | 1 | 0 | 0 |
| March2024 | 7090 | 7011 | 609 | 4 | 0 | 0 |

These checks establish adapter-level visibility consistency, not historical factual validity or browser rendering support.

## Execution provenance and limitations

Playwright skill instructions were read. `npx` and Node.js were present. An initial npm CLI attempt could not write the default npm cache; no dependencies were installed. The already cached Playwright package was used directly with the already installed Chromium executable because its default browser revision was unavailable. Actual paths used:

```text
Node.js v24.18.0
C:/Users/86185/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/playwright
C:/Users/86185/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe
```

The screenshot/audit tool accepts explicit module/executable paths so the release has no hidden dependence on those local cache locations. They are optional render-time dependencies; graph generation and numerical chart validation remain standard-library-only. The actual before/after SVGs and PNGs were inspected locally. External-model review capabilities and any separate image review are recorded in the multi-model logs, not inferred here.

## Reproducibility result

`portable_reproduction.json` records an executed clean-copy verification: source/tests and separate real inputs copied to a new temporary directory, no output/cache copied, generation executed twice with seed 42, all six output file hashes identical to each other and the revised delivered outputs, copied test suite 53/53 passed with no skips. No hard links were used. This verifies clean directory execution in CPython 3.10.0 on this Windows host; independent OS/interpreter installations remain untested. The ZIP itself intentionally omits original inputs but includes their complete sizes/hashes in its manifest.

# StatPro

StatPro is a local-first manufacturing analytics platform for statistical process control, DOE, measurement systems analysis, reliability, and FMEA workflows.

The repository starts with a dependency-free Python statistical core so formulas and result contracts can be independently verified before UI and service adapters are added.

## Implemented

- Reproducible `ResultBundle` with input SHA-256, engine version, warnings, and public-source provenance
- Individuals and Moving Range (I-MR) control chart with selectable 3-sigma-only, NIST/Western Electric, or Nelson eight-test rules
- Xbar-R control chart for constant subgroup sizes 2–10 with Nelson tests 1–8 on Xbar and tests 1–4 on R
- Normal capability for individual observations with within/overall variation kept distinct
- Reproducible two-level full factorial DOE analysis plus regular fractional-factorial generation with defining relations, resolution, and main/two-factor alias structures
- Balanced crossed Gage R&R using two-way random-effects ANOVA variance components
- Immutable CSV Dataset snapshots and revisioned Worksheet cell edits
- Packaged Draft 2020-12 `ResultBundle` JSON Schema
- Immutable Design/Process FMEA study revisions with action ownership, completion evidence, risk reassessment, review, approval, and audit history
- Versioned external Action Priority policy contract without bundled proprietary decision tables
- Loopback-only FastAPI adapter with Analysis Run, revisioned Worksheet/FMEA storage, ETags, optimistic concurrency, and cursor paging
- Atomic local JSON document adapter plus an in-memory contract-test adapter
- React workbench with dashboard, CSV Worksheet import/editing, I-MR setup/results, DOE analysis/fractional-design/response-optimizer flows, FMEA list/editor/review flow, provenance drawer, theme, and connection states
- Accessible control-chart summaries and table alternatives with a 768px minimum supported viewport
- Typed validation errors
- JSON CLI
- Unit tests using NIST examples and hand-calculated fixtures

## Run

```powershell
py -3.12 -m unittest discover -s tests -v
$env:PYTHONPATH = "src"
py -3.12 -m statpro.cli imr --input samples\imr-nist.json
py -3.12 -m statpro.cli xbar-r --input samples\xbar-r.json
py -3.12 -m statpro.cli capability-normal --input samples\capability-normal.json
py -3.12 -m statpro.cli doe-full-factorial --input samples\doe-full-factorial.json
py -3.12 -m statpro.cli doe-fractional-factorial --input samples\doe-fractional-factorial.json
py -3.12 -m statpro.cli doe-analyze-full-factorial --input samples\doe-full-factorial-analysis.json
py -3.12 -m statpro.cli doe-optimize-responses --input samples\doe-response-optimizer.json
py -3.12 -m statpro.cli gage-rr-crossed --input samples\gage-rr-crossed.json
py -3.12 -m statpro.cli dataset-import-csv --input samples\process-data.csv
```

## Local API

```powershell
py -3.12 -m pip install -e ".[api]"
statpro-api --storage "D:\StatProData" --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765/docs` for the generated OpenAPI interface. The launcher rejects non-loopback hosts. Analysis Run IDs are immutable; use a new ID for recalculation.

## Local Web UI

Run the API first, then open a second PowerShell window:

```powershell
cd web
npm ci
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to the loopback API on port 8765. Use `npm run check` for the UI tests, TypeScript check, and production build.

## Principles

- Public formulas and standards are the implementation source.
- Third-party binary internals and proprietary UI assets are not product-code inputs.
- Missing data is explicit and never silently replaced with zero.
- Control limits and specification limits are separate domain concepts.
- Every result remains traceable to exact inputs and engine behavior.

See `CONTEXT-MAP.md` for bounded-context ownership and `docs/01.StatPro_SRS.md` through `docs/07.StatPro_Test_Report.md` for the staged development record.

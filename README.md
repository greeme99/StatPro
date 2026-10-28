# StatPro

StatPro is a local-first manufacturing analytics platform for statistical process control, DOE, measurement systems analysis, reliability, and FMEA workflows.

The repository starts with a dependency-free Python statistical core so formulas and result contracts can be independently verified before UI and service adapters are added.

## Implemented

- Reproducible `ResultBundle` with input SHA-256, engine version, warnings, and public-source provenance
- Individuals and Moving Range (I-MR) control chart with selectable 3-sigma-only, NIST/Western Electric, or Nelson eight-test rules
- Xbar-R control chart for constant subgroup sizes 2–10 with Nelson tests 1–8 on Xbar and tests 1–4 on R
- Xbar-S control chart for constant subgroup sizes 2–100 using c4-corrected sigma, with Nelson tests 1–8 on Xbar and tests 1–4 on S
- Startup-adjusted EWMA chart for individual observations with historical or explicitly estimated center/sigma and configurable lambda/L
- Standardized two-sided tabular CUSUM for individual observations with historical or explicitly estimated target/sigma and configurable k/h
- Binomial p/np and Poisson c/u attribute control charts with pooled Phase I centers, opportunity-specific limits for p/u, constant-opportunity enforcement for np/c, and accessible chart/table results
- Laney P′/U′ charts with moving-range Sigma Z adjustment for overdispersion and underdispersion
- Normal capability for individual observations with within/overall variation kept distinct, plus empirical non-normal Cnp/Cnpk/Cnpm capability with explicit tail-quantile limitations
- Reproducible two-level full factorial DOE analysis with deterministic automatic blocking and factor-constrained multi-response desirability optimization, regular fractional-factorial generation/main-effect analysis with bounded automatic minimum-run/minimum-aberration generator selection, explicit regular block generators, blocked full resolution-III foldover and single-factor foldover, 3–5 factor Box–Behnken and central-composite response-surface designs with complete-quadratic modelling, stationary-point/canonical analysis, bounded two-factor surface grids, accessible iso-response contours and projected 3D wireframes, plus Plackett–Burman screening design/response analysis from 12 to 48 runs
- Versioned DOE report projection with immutable Run identity, semantic HTML, JSON, and UTF-8 CSV tables in a deterministic ZIP export
- Balanced crossed Gage R&R using two-way random-effects ANOVA variance components
- Immutable CSV Dataset snapshots and revisioned Worksheet cell edits
- Packaged Draft 2020-12 `ResultBundle` JSON Schema
- Immutable Design/Process FMEA study revisions with an evidence-derived AIAG/VDA seven-step progress view, action ownership, completion evidence, risk reassessment, review, approval-time reauthentication, and audit history
- Immutable external Action Priority policy import, version/digest validation, Study attachment, audit history, and automatic reuse without bundled proprietary decision tables
- Process Flow → characteristic → PFMEA → Control Plan ID traceability with revision history, link validation, reaction-plan ownership, and stored SPC/MSA Run references rechecked in review reports
- Loopback-only FastAPI adapter with Analysis Run, revisioned Worksheet/FMEA storage, ETags, optimistic concurrency, and cursor paging
- Atomic local JSON document adapter plus an in-memory contract-test adapter
- React workbench with dashboard, CSV Worksheet import/editing, I-MR, Xbar-S, EWMA, CUSUM, and p/np/c/u setup/results, DOE analysis/fractional/Plackett–Burman/Box–Behnken/response-optimizer flows, FMEA seven-step/editor/review, external AP policy management, PFMEA/Control Plan traceability, provenance drawer, theme, and connection states
- Accessible control-chart summaries and table alternatives with a 768px minimum supported viewport
- Typed validation errors
- JSON CLI
- Unit tests using NIST examples and hand-calculated fixtures

## Run

```powershell
py -3.12 -m unittest discover -s tests -v
$env:PYTHONPATH = "src"
py -3.12 -m statpro.cli imr --input samples\imr-nist.json
py -3.12 -m statpro.cli p-chart --input samples\p-chart.json
py -3.12 -m statpro.cli np-chart --input samples\np-chart.json
py -3.12 -m statpro.cli c-chart --input samples\c-chart.json
py -3.12 -m statpro.cli u-chart --input samples\u-chart.json
py -3.12 -m statpro.cli laney-p-prime --input samples\laney-p-prime.json
py -3.12 -m statpro.cli laney-u-prime --input samples\laney-u-prime.json
py -3.12 -m statpro.cli xbar-r --input samples\xbar-r.json
py -3.12 -m statpro.cli xbar-s --input samples\xbar-s.json
py -3.12 -m statpro.cli ewma --input samples\ewma.json
py -3.12 -m statpro.cli cusum --input samples\cusum.json
py -3.12 -m statpro.cli capability-normal --input samples\capability-normal.json
py -3.12 -m statpro.cli capability-nonnormal --input samples\capability-nonnormal.json
py -3.12 -m statpro.cli doe-full-factorial --input samples\doe-full-factorial.json
py -3.12 -m statpro.cli doe-full-factorial --input samples\doe-full-factorial-blocked.json
py -3.12 -m statpro.cli doe-fractional-factorial --input samples\doe-fractional-factorial.json
py -3.12 -m statpro.cli doe-fractional-factorial --input samples\doe-fractional-factorial-blocked.json
py -3.12 -m statpro.cli doe-fractional-factorial --input samples\doe-fractional-factorial-partial-foldover.json
py -3.12 -m statpro.cli doe-fractional-factorial-auto --input samples\doe-fractional-factorial-auto.json
py -3.12 -m statpro.cli doe-analyze-fractional-factorial --input samples\doe-fractional-factorial-analysis.json
py -3.12 -m statpro.cli doe-box-behnken --input samples\doe-box-behnken.json
py -3.12 -m statpro.cli doe-explore-box-behnken --input samples\doe-box-behnken-surface.json
py -3.12 -m statpro.cli doe-analyze-central-composite --input samples\doe-central-composite-analysis.json
py -3.12 -m statpro.cli doe-explore-central-composite --input samples\doe-central-composite-surface.json
py -3.12 -m statpro.cli doe-plackett-burman --input samples\doe-plackett-burman.json
py -3.12 -m statpro.cli doe-analyze-plackett-burman --input samples\doe-plackett-burman-analysis.json
py -3.12 -m statpro.cli doe-analyze-full-factorial --input samples\doe-full-factorial-analysis.json
py -3.12 -m statpro.cli doe-optimize-responses --input samples\doe-response-optimizer.json
py -3.12 -m statpro.cli gage-rr-crossed --input samples\gage-rr-crossed.json
py -3.12 -m statpro.cli dataset-import-csv --input samples\process-data.csv
```

## Local API

```powershell
py -3.12 -m pip install -e ".[api]"
statpro-approval-user --file "D:\StatProData\approval-identities.json" --user-id quality.approver --display-name "Quality Approver"
statpro-api --storage "D:\StatProData" --host 127.0.0.1 --port 8765
```

The identity command prompts twice for a password and stores only a salted scrypt verifier. Restart the API after changing the identity file. Open `http://127.0.0.1:8765/docs` for the generated OpenAPI interface. The launcher rejects non-loopback hosts. Analysis Run IDs are immutable; use a new ID for recalculation.

For an existing DOE Run, download its human-readable report or portable export bundle:

```powershell
Invoke-WebRequest http://127.0.0.1:8765/v1/analysis-runs/doe-001/report.html -OutFile doe-001-report.html
Invoke-WebRequest http://127.0.0.1:8765/v1/analysis-runs/doe-001/export -OutFile doe-001-export.zip
```

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

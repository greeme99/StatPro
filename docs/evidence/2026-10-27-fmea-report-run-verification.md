# FMEA report-time SPC/MSA Run identity verification

## Authority boundary

The public AIAG/VDA basis for PFMEA–Control Plan traceability is recorded in [the original traceability evidence](2026-10-25-pfmea-control-plan-traceability.md). It does not specify how StatPro must identify or recheck stored analysis results. Available Minitab 14 static/dynamic evidence still does not establish an FMEA Control Plan or linked Run feature. This is an independent StatPro integrity check, not a Minitab behavior claim.

## Behavior

On each `GET /v1/fmea-studies/{study_id}/report`, the API loads each distinct referenced Run once and compares its Run ID, analysis type, input digest, and storage ETag with the reference recorded in that FMEA revision. The report provides a check per Control Plan reference: `verified`, `missing`, `mismatch`, or `unavailable` (unreadable or invalid owned identity fields). It retains the FMEA rows even when evidence cannot be verified, making the failure visible. Reports built directly from an isolated Study without storage access carry `analysis_evidence_checks: null` rather than claiming verification.

The report ETag hashes the complete report response, so a changed verification status changes the ETag even if the FMEA Study revision is unchanged. The workbench shows each status in a keyboard-accessible table. These checks establish stored document identity only; they do not judge statistical suitability, gauge validity, control-chart stability, or correspondence between Run inputs and the Control Plan characteristic. Approval remains self-reported and does not yet enforce verified evidence.

## Verification

- API integration: linked SPC and MSA Runs both verify; external content change produces `mismatch` and a new report ETag; invalid owned identity produces `unavailable`; deletion produces `missing`.
- Web UI: the report displays a mismatched Run as `내용 불일치` in an accessible table.
- Full regression: Python 168 tests, React/Vitest 52 tests, Ruff, Python compileall, TypeScript/Vite build, and `git diff --check` passed.

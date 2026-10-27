# PFMEA Control Plan → stored SPC/MSA Run evidence

## Public basis and scope

AIAG describes the Control Plan as linked to APQP processes and its PFMEA training explicitly covers PFMEA–Control Plan linkages. VDA QMC guidance describes Control Plan monitoring methods and reaction plans with FMEA as an input. See the public source links and scope limits in [the process traceability evidence](2026-10-25-pfmea-control-plan-traceability.md). These sources justify traceability as a manufacturing quality workflow; they do not prescribe StatPro's Run ID, ETag, input digest, API, or UI.

## Minitab 14 boundary

The available Minitab 14 static/dynamic evidence does not confirm a PFMEA or Control Plan feature, nor any SPC/MSA-to-FMEA linkage. This increment is an independent StatPro implementation. No Minitab-specific behavior, file format, or interface compatibility is claimed.

## StatPro implementation

- A draft Process FMEA Control Plan item may link a previously stored Analysis Run. The API loads that Run, checks its owned document shape, and accepts only `spc.*` or `msa.*` analysis types. A missing Run, duplicate link on the same Control Plan item, or DOE Run is rejected.
- The reference stores the Run ID, analysis type, storage ETag, and input digest. The client supplies only the Run ID; the server derives the other fields from the stored Run.
- Linking creates a new FMEA revision and audit event, with optimistic storage-version concurrency. Existing Control Plan snapshots lacking `analysis_evidence` load with an empty collection.
- The revision report and UI project the same stored reference. Report generation does not fetch or revalidate the Run at read time. Actor names are self-reported workflow fields, not authenticated signatures.

The evidence reference proves which Run document was observed when linked. It does not prove metrological suitability, SPC process stability, or that the Run's input belongs to the same characteristic. Those checks require a later explicit workflow contract.

## Verification

- Python full suite: 168 tests passed, including SPC and MSA linking, report projection, duplicate/missing/unsupported Run rejection, stale-version rejection, and old-snapshot loading.
- React/Vitest: 52 tests passed, including Control Plan Run linking and display.
- Ruff, Python compileall, TypeScript/Vite build, and `git diff --check`: passed.

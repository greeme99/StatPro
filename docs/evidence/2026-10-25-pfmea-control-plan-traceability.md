# PFMEA process-flow and Control Plan traceability evidence boundary

## Scope

This increment adds an explicit, revisioned trace chain from Process Flow to Process Characteristic, PFMEA Failure Analysis, and Control Plan item. It does not copy proprietary forms, classifications, decision tables, or product UI.

## Public workflow evidence

- AIAG's official Control Plan manual page describes the Control Plan as linked with APQP processes and identifies software management as part of the current first-edition scope: https://www.aiag.org/training-and-resources/manuals/details/CP-1
- AIAG's official PFMEA training description explicitly covers the linkages between Process FMEAs and Control Plans: https://www.aiag.org/training-and-resources/training-catalog/details/VFUP?CourseCode=LAIAT
- VDA QMC public material identifies Process Flow Diagram, PFMEA, and Control Plan as related deliverables and states that the Control Plan reflects the process while considering FMEA findings: https://vda-qmc.de/wp-content/uploads/2026/01/VDA-2_Yellow-Volume_7th-edition-2025-1.pdf
- VDA QMC public guidance describes Control Plan monitoring of product and process characteristics, inspection methods, and reaction plans by process step, with FMEA as an input: https://vda-qmc.de/wp-content/uploads/2023/01/VDA_Volume_Assessment_of_Quality_Management_Methods__Guideline__1st_Edition__November_2017__Online-Document.pdf

These sources establish the workflow relationship and minimum record concepts. They do not establish proprietary field layouts, special-characteristic symbols, AP matrices, or customer-specific approval rules.

## Minitab 14 evidence

The current Minitab 14 static and dynamic evidence has not established an FMEA-specific Process Flow, PFMEA, or Control Plan implementation, dialog, session command, file record, or algorithm. This is a bounded negative search result, not proof of absence. The feature is classified as an independent StatPro manufacturing-quality capability and is not represented as reconstructed Minitab behavior.

## Independent StatPro implementation

- `ProcessStep` owns a stable step ID, sequence, name, and operation.
- `ProcessCharacteristic` owns a stable characteristic ID and references exactly one Process Step.
- `FailureAnalysis` can reference one Process Step and a deduplicated set of characteristic IDs. If a process flow exists, the step reference is required and every characteristic must belong to that step.
- `ControlPlanItem` references one characteristic and one or more PFMEA Failure Analysis IDs. Every referenced failure must explicitly link the same step and characteristic.
- All additions create a new immutable Study revision, preserve the parent digest, append an actor/time audit event, and use optimistic storage-version concurrency at the API boundary.
- The React workbench exposes token-based editors and an accessible table that projects the ID chain. It does not infer links from similar text.
- Older snapshots remain readable because all new collections and failure-link fields have explicit empty defaults.

The IDs are reusable integration seams for later SPC/MSA evidence links, report generation, approvals, and customer-specific Control Plan fields without coupling those modules to FMEA storage internals.

## Verification

- Python domain/API suite: 130 tests passed.
- Ruff: passed.
- React/Vitest: 39 tests passed.
- TypeScript/Vite production build: passed.
- Python compileall and `git diff --check`: passed.

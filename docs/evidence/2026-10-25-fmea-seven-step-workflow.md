# FMEA seven-step workflow evidence boundary

## Scope

This increment exposes a deterministic seven-step progress view for Design and Process FMEA studies. It does not bundle or reconstruct proprietary Severity, Occurrence, Detection, or Action Priority decision tables.

## Public standards evidence

AIAG publicly describes the harmonized seven-step approach as Planning and Preparation, Structure Analysis, Function Analysis, Failure Analysis, Risk Analysis, Optimization, and Results Documentation:

- https://blog.aiag.org/its-here...claim-your-copy-of-the-new-aiag-vda-fmea-handbook-today
- https://www.aiag.org/docs/default-source/quality-/new_aiag_vda_fmea_-whitepaper.pdf

VDA QMC independently publishes the same seven-step sequence in its public overview:

- https://vda-qmc.de/wp-content/uploads/2024/04/VDA-QMC-White-Paper-FMEA-Englisch-24.pdf

These sources establish public workflow names and ordering only. They do not authorize copying proprietary handbook tables or licensed form content.

## Minitab 14 evidence

No FMEA-specific Minitab 14 symbol, dialog, session command, file structure, or numeric algorithm has been established by the current static evidence. This is a bounded negative result, not proof that no related capability exists. The StatPro FMEA module is therefore classified as an independent manufacturing-quality requirement, not as a reconstructed Minitab feature.

## Independent StatPro implementation

`FmeaStudySnapshot.seven_step_progress` projects owned Study facts into the public seven-step vocabulary:

1. Study creation establishes Planning and Preparation.
2. Existing failure-analysis items establish Structure, Function, Failure, and Risk Analysis because the current item contract requires each corresponding field and S/O/D/control data together.
3. Recommended-action lifecycle establishes Optimization as not started, in progress, or complete.
4. Review and approval state plus audit events establish Results Documentation.

The projection is not persisted as a second mutable truth. Older snapshots remain readable, revisions remain immutable, and future process-flow, characteristic, Control Plan, and report entities can replace the coarse evidence counts without changing the seven-step API vocabulary.

## Verification

- Python domain/API suite: 124 tests passed.
- Ruff: passed.
- Python compileall: passed.
- React/Vitest: 37 tests passed.
- TypeScript/Vite production build: passed.

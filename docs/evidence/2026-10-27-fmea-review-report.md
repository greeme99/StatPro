# FMEA revision review report

## Public reference

AIAG describes the FMEA seven-step process, including Results Documentation, and notes both spreadsheet form sheets and software report views. Its errata says Step 7 summarizes PFMEA scope and results for management/customer review. These statements support a review report workflow, not a proprietary form layout or certification claim.

- https://blog.aiag.org/its-here...claim-your-copy-of-the-new-aiag-vda-fmea-handbook-today
- https://www.aiag.org/docs/default-source/training-and-resources/erratta-documents/aiag-vda-fmea-handbook-errata-june-2020.pdf
- https://www.aiag.org/training-and-resources/manuals/details/FMEAAV-1

## Minitab 14 boundary

No Minitab 14 FMEA report UI, binary record, or session behavior has been established. This is an independent StatPro manufacturing-quality feature and makes no Minitab 14 equivalence claim.

## StatPro implementation

`build_study_report` projects one stored revision with its digest, seven-step progress, failure analyses, current ratings and AP, linked process step/characteristics/Control Plan items, actions, audit events, and approval event if recorded. Joining uses owned IDs; the projection does not persist a second copy of the study. `GET /v1/fmea-studies/{study_id}/report` exposes the report, and the workbench presents its current revision in an accessible table with empty, loading, and error states.

The original approval event recorded a self-reported actor and time. A later increment added approval-time local password reauthentication, `fmea_approver` authorization, server time, signature meaning, signer manifestation, and linkage to the signed revision digest. Legacy approvals remain readable and are explicitly identified as unauthenticated. See [the electronic approval evidence](2026-10-27-fmea-electronic-approval.md), [the linkage evidence](2026-10-27-fmea-spc-msa-run-evidence.md), and [the report verification evidence](2026-10-27-fmea-report-run-verification.md). Run identity checks do not establish analytical suitability.

## Verification

- API integration test checks a process step, characteristic, failure, and Control Plan join against the stored snapshot digest.
- UI test checks the current revision report and empty state.
- Approval integration tests check reauthentication, authority, signed revision identity, linked Run revalidation, and report manifestation.

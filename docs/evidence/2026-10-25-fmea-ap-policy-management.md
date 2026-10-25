# FMEA external Action Priority policy management evidence boundary

## Scope

This increment makes the existing external `ActionPriorityPolicy` contract usable through the local API and React workbench. It stores only entries supplied by an authorized user. StatPro does not ship, infer, scrape, or reconstruct proprietary Severity, Occurrence, Detection, or Action Priority tables.

## Public workflow evidence

AIAG's public description identifies Action Priority as part of the harmonized FMEA approach and distinguishes the seven-step workflow:

- https://blog.aiag.org/its-here...claim-your-copy-of-the-new-aiag-vda-fmea-handbook-today
- https://www.aiag.org/docs/default-source/quality-/new_aiag_vda_fmea_-whitepaper.pdf

The public material establishes that AP participates in Risk Analysis and Optimization. It does not provide a redistributable AP decision matrix for this repository.

## Minitab 14 evidence

The current Minitab 14 static evidence has not established an FMEA or Action Priority implementation, dialog, command, file record, or algorithm. This remains a bounded negative search result. The feature is an independent StatPro manufacturing-quality capability and is not represented as Minitab-compatible behavior.

## Independent StatPro implementation

- An imported policy is normalized and stored as an immutable document keyed by its SHA-256 content identity.
- The policy retains a human-facing policy ID separately from its lookup key and exact digest.
- A Study can attach only a policy whose standard version matches the Study.
- Attachment creates a new Study revision, records actor/time/key/digest in the audit trail, and reassesses existing current ratings.
- Later failure analyses and completed-action reassessments resolve the attached lookup key and verify policy ID and digest before evaluation.
- Missing combinations remain explicit as `no_matching_entry`; absence of a policy remains `policy_not_supplied`.
- The UI imports comma, tab, or semicolon separated `S,O,D,priority` rows and only offers compatible policy revisions for attachment.

## Verification

- Python domain/API suite: 127 tests passed.
- Ruff: passed.
- React/Vitest: 38 tests passed.
- TypeScript/Vite production build: passed.
- Python compileall: passed.

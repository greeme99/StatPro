# SPC stage and historical-parameter contract

## Scope

This increment adds an explicit Phase 1/Phase 2 contract to the I-MR, EWMA, and standardized tabular CUSUM engines. Phase 1 is a baseline-estimation workflow: missing center and sigma are estimated from the supplied observations. Phase 2 is prospective monitoring: historical center and process sigma are mandatory and are carried into the ResultBundle parameters with `mean_source` and `sigma_source` set to `historical`.

The contract is independent of Minitab implementation details and is designed to remain stable as subgroup, attribute, and future stage-aware charts are added.

## Implemented behavior

- `stage` accepts only `phase_1` or `phase_2`.
- Phase 2 rejects a missing `target` or `sigma` with `historical_parameters_required`.
- I-MR accepts an explicit historical `sigma`; its individual limits use that value and its moving-range center and UCL use `d2 × sigma` and `D4 × d2 × sigma`. The average moving range of monitored observations remains a separate diagnostic.
- EWMA uses the historical target and sigma for startup-adjusted limits in Phase 2.
- CUSUM uses the historical target and sigma for standardized accumulation in Phase 2.
- ResultBundle parameters preserve `stage`, `mean_source`, `sigma_source`, and the resolved `process_sigma`.
- API and CLI payloads expose the same contract; omitted `stage` remains backward-compatible with Phase 1.

## Evidence boundaries

- Public statistical basis: SPC Phase 1 estimation and Phase 2 prospective monitoring are standard statistical workflow concepts; the implementation cites the existing NIST/Minitab method sources already attached to each chart.
- Minitab 14 evidence: no new dynamic observation was performed in this increment. Existing Minitab 14 static evidence only establishes candidate SPC entry points, not this exact stage contract. Therefore Minitab 14 equivalence remains unconfirmed.
- StatPro evidence: `tests/test_spc.py` verifies required historical parameters, provenance fields, and historical-limit calculation; API regression coverage remains green.

## Verification

Executed on 2026-10-27:

- `python -m unittest tests.test_spc tests.test_api -q` — 59 tests passed
- `python -m compileall -q src tests` — passed
- `python -m ruff check src tests` — passed

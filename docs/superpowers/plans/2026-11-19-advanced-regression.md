# Advanced Regression Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend StatPro's executable regression workflow with influence diagnostics, validated model selection, best-subset comparison, and categorical/GLM support.

**Architecture:** Keep the immutable `ResultBundle` boundary. Extend `src/statpro/analyses/regression.py` with explicit, bounded algorithms; expose each completed method through the FastAPI analysis-run endpoints; then connect the existing React setup/result/export path. Preserve OLS as the shared numerical primitive and use no new dependencies.

**Tech Stack:** Python 3.11 standard library, FastAPI/Pydantic, unittest, React/TypeScript/Vite/Vitest.

**Spec:** User request of 2026-11-19: implement the previously proposed regression items 1–5 in order; Minitab official regression documentation consulted as comparative scope, not copied implementation.

## Global Constraints

- No new runtime dependency; use existing numerical primitives and `ResultBundle` contracts.
- Keep user-visible guidance in Korean and use the existing StatPro design tokens.
- Do not claim Minitab equivalence until behavior is independently tested and documented.
- Bound exhaustive computations by documented predictor limits; reject unsupported inputs explicitly.
- Preserve unrelated working-tree changes and commit only each task's files.

## Review Focus

- Near-perfect fit and zero residual variance must not yield fabricated influence statistics.
- Singular, collinear, or insufficient-observation designs must remain rejected before selection or validation.
- Selection must retain lower-order terms when a hierarchy-constrained interaction is retained.
- Holdout and fold assignment must be deterministic from the immutable input, with no leakage between train and test rows.
- Categorical levels absent from an inference/validation row must report a controlled unsupported-level error rather than silently recoding data.

---

### Task 1: OLS influence diagnostics

**Files:**
- Modify: `src/statpro/analyses/regression.py`
- Modify: `tests/test_regression.py`
- Modify: `web/src/pages/ResultPage.tsx`
- Modify: `web/src/regressionExport.ts`
- Test: `web/src/regressionExport.test.ts`

**Interfaces:**
- Produces: `fitted_values` rows with `standardized_residual`, `studentized_residual`, `cooks_distance`, and `dffits`; `diagnostics.influence_thresholds`.

- [ ] Write failing core and export/result tests for an OLS data set with a high-influence row.
- [ ] Run the focused tests and verify the new fields are absent.
- [ ] Add bounded OLS influence calculations, nulling undefined measures when residual degrees of freedom or leverage prevents valid computation.
- [ ] Present an accessible influence table and include the fields in the HTML export.
- [ ] Run focused backend/frontend checks and commit `feat(regression): add influence diagnostics`.

### Task 2: Hierarchical stepwise model selection

**Files:**
- Modify: `src/statpro/analyses/regression.py`
- Modify: `src/statpro/api/app.py`
- Modify: `src/statpro/analyses/__init__.py`
- Modify: `tests/test_regression.py`
- Modify: `tests/test_api.py`
- Modify: `web/src/api.ts`
- Modify: `web/src/App.tsx`
- Modify: `web/src/pages/AnalysisSelectionPage.tsx`
- Modify: `web/src/pages/BasicAnalysisSetupPage.tsx`
- Modify: `web/src/pages/ResultPage.tsx`

**Interfaces:**
- Consumes: Task 1's OLS result rows unchanged.
- Produces: `stepwise_ols(response, predictors, method, criterion, alpha_enter, alpha_remove, interaction_terms)` returning `regression.stepwise_ols` with per-step selection history and AICc/BIC.

- [x] Write failing tests for forward selection, backward removal, and mandatory lower-order terms for a selected interaction.
- [x] Run focused tests and verify no stepwise adapter exists.
- [x] Implement bounded, deterministic hierarchical forward/backward/stepwise selection (20 candidate expanded terms maximum), with explicit AICc/BIC diagnostics.
- [x] Add the analysis-run endpoint and a Korean setup/result workflow.
- [x] Run backend/API/frontend focused checks and commit `feat(regression): add hierarchical stepwise selection`.

### Task 3: Holdout and k-fold validation

**Files:**
- Modify: `src/statpro/analyses/regression.py`
- Modify: `src/statpro/api/app.py`
- Modify: `tests/test_regression.py`
- Modify: `tests/test_api.py`
- Modify: `web/src/api.ts`
- Modify: `web/src/pages/BasicAnalysisSetupPage.tsx`
- Modify: `web/src/pages/ResultPage.tsx`

**Interfaces:**
- Consumes: Task 2's selected-term model configuration.
- Produces: deterministic validation diagnostics `rmse`, `mae`, `r_squared_pred`, fold/holdout sizes, and per-fold summary tables.

- [ ] Write failing tests for deterministic 5-fold validation, holdout metrics, and insufficient data rejection.
- [ ] Run focused tests and verify validation diagnostics are absent.
- [ ] Implement row-index deterministic holdout/k-fold evaluation that refits only on train rows and aggregates held-out predictions.
- [ ] Present validation summaries in the result workflow.
- [ ] Run backend/API/frontend focused checks and commit `feat(regression): add model validation metrics`.

### Task 4: Best subsets comparison

**Files:**
- Modify: `src/statpro/analyses/regression.py`
- Modify: `src/statpro/api/app.py`
- Modify: `src/statpro/analyses/__init__.py`
- Modify: `tests/test_regression.py`
- Modify: `tests/test_api.py`
- Modify: `web/src/api.ts`
- Modify: `web/src/App.tsx`
- Modify: `web/src/pages/AnalysisSelectionPage.tsx`
- Modify: `web/src/pages/BasicAnalysisSetupPage.tsx`
- Modify: `web/src/pages/ResultPage.tsx`

**Interfaces:**
- Consumes: OLS fit statistics and Task 3 validation metric conventions.
- Produces: `best_subsets_ols` returning ranked models with adjusted R², predicted R², PRESS, Mallows' Cp, AICc, BIC, and condition number.

- [ ] Write failing tests for ranking a known two-predictor model and rejecting more than 15 candidate predictors.
- [ ] Run focused tests and verify no best-subsets route exists.
- [ ] Enumerate every non-empty subset for at most 15 continuous X variables, skip singular candidates with recorded counts, and retain the requested top models by size.
- [ ] Add a comparison result table with selected-model handoff to the standard OLS workspace.
- [ ] Run backend/API/frontend focused checks and commit `feat(regression): add best subsets comparison`.

### Task 5: Categorical predictors and initial GLM expansion

**Files:**
- Modify: `src/statpro/analyses/regression.py`
- Modify: `src/statpro/api/app.py`
- Modify: `src/statpro/analyses/__init__.py`
- Modify: `tests/test_regression.py`
- Modify: `tests/test_api.py`
- Modify: `web/src/api.ts`
- Modify: `web/src/App.tsx`
- Modify: `web/src/pages/BasicAnalysisSetupPage.tsx`
- Modify: `web/src/pages/ResultPage.tsx`
- Modify: `docs/11.StatPro_Development_Roadmap.md`

**Interfaces:**
- Consumes: OLS/IRLS patterns from existing linear and binary logistic paths.
- Produces: explicit reference-coded categorical X expansion for OLS and binary logistic; a bounded Poisson log-link GLM for non-negative count Y, with coefficient inference and fitted values.

- [ ] Write failing tests for reference level coding, an unseen categorical level rejection, and a Poisson count fit.
- [ ] Run focused tests and verify categorical/Poisson routes do not exist.
- [ ] Implement explicit input contracts for numeric/categorical predictors and a bounded Poisson IRLS solver; retain ordinal/multinomial/mixed models as out of scope.
- [ ] Add setup validation, Korean result guidance, and report-compatible tables.
- [ ] Run backend/API/frontend focused checks, update roadmap scope truthfully, and commit `feat(regression): add categorical and poisson models`.

## Execution order

- [x] Task 1
- [ ] Task 2
- [ ] Task 3
- [ ] Task 4
- [ ] Task 5

Ruling: Task 5 means categorical X plus Poisson GLM only, not all Minitab generalized/mixed/ordinal regression families — the latter require distinct likelihoods and validation contracts.

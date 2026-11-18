import { describe, expect, it } from "vitest";
import { regressionPrintHtml, toRegressionExportView } from "./regressionExport";
import type { ResultBundle } from "./types";

const result: ResultBundle = {
  analysis_type: "regression.linear_ols",
  engine_version: "0.6.0",
  input_digest: "d".repeat(64),
  parameters: {},
  diagnostics: { prediction_interval_confidence: 0.95, maximum_vif: 2.4, influence_thresholds: { cooks_distance: 0.5 } },
  tables: {
    fitted_values: { rows: [{ observation: 1, fitted: 10, residual: -0.5, prediction_interval_lower: 7.1, prediction_interval_upper: 12.9, standardized_residual: -0.4, studentized_residual: -0.42, cooks_distance: 0.12, dffits: -0.21 }] },
    collinearity: { rows: [{ term: "온도", vif: 2.4, tolerance: 0.4167 }] },
  },
  plots: {},
  warnings: [],
  assumptions: [],
  provenance: [],
};

describe("OLS regression report", () => {
  it("includes stored collinearity and prediction-interval evidence", () => {
    const report = regressionPrintHtml("ols-001", result, toRegressionExportView(result)!);

    expect(report).toContain("공선성 진단");
    expect(report).toContain("VIF");
    expect(report).toContain("온도");
    expect(report).toContain("관측별 예측구간 (95%)");
    expect(report).toContain("7.1000");
    expect(report).toContain("12.9000");
    expect(report).toContain("영향 관측치 진단");
    expect(report).toContain("Cook");
  });

  it("reuses the OLS export for a two-factor interaction model", () => {
    expect(toRegressionExportView({ ...result, analysis_type: "regression.interaction_ols" })).not.toBeNull();
  });
});

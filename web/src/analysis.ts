import type { ResultBundle } from "./types";

export type ProcessPoint = { index: number; value: number; signal: boolean };

export type ImrView = {
  points: ProcessPoint[];
  center: number;
  ucl: number;
  lcl: number;
};

export function toImrView(result: ResultBundle | undefined): ImrView | null {
  if (!result || result.analysis_type !== "spc.imr") return null;

  const values = result.plots.individuals?.values;
  const signals = result.plots.individuals?.signals;
  const limits = result.tables.limits?.individuals;
  if (!Array.isArray(values) || !Array.isArray(signals) || !limits) return null;
  if (![limits.center, limits.ucl, limits.lcl].every(Number.isFinite)) return null;

  const signalIndices = new Set<number>(signals);
  const points = values
    .filter((value: unknown): value is number => typeof value === "number" && Number.isFinite(value))
    .map((value: number, zeroBasedIndex: number) => ({
      index: zeroBasedIndex + 1,
      value,
      signal: signalIndices.has(zeroBasedIndex),
    }));

  return { points, center: limits.center, ucl: limits.ucl, lcl: limits.lcl };
}

export type DoeCoefficient = {
  term: string;
  order: number;
  coefficient: number;
  effect: number | null;
  sum_of_squares: number | null;
  f_value: number | null;
  p_value: number | null;
};

export type DoeAnovaRow = {
  source: string;
  degrees_of_freedom: number;
  sum_of_squares: number;
  mean_square: number | null;
  f_value: number | null;
  p_value: number | null;
};

export type DoeResidual = {
  run_order: number;
  standard_order: number | null;
  point_type: string;
  observed: number;
  fitted: number;
  residual: number;
  scaled_residual: number | null;
};

export type DoeView = {
  coefficients: DoeCoefficient[];
  anova: DoeAnovaRow[];
  residuals: DoeResidual[];
  rSquared: number | null;
  adjustedRSquared: number | null;
  residualStandardDeviation: number | null;
  responseName: string;
};

export function toDoeView(result: ResultBundle | undefined): DoeView | null {
  if (!result || result.analysis_type !== "doe.full_factorial_2level_analysis") return null;
  const coefficients = result.tables.coefficients;
  const anova = result.tables.anova;
  const residuals = result.tables.residuals;
  if (!Array.isArray(coefficients) || !Array.isArray(anova) || !Array.isArray(residuals)) return null;
  return {
    coefficients: coefficients as DoeCoefficient[],
    anova: anova as DoeAnovaRow[],
    residuals: residuals as DoeResidual[],
    rSquared: typeof result.diagnostics.r_squared === "number" ? result.diagnostics.r_squared : null,
    adjustedRSquared: typeof result.diagnostics.adjusted_r_squared === "number" ? result.diagnostics.adjusted_r_squared : null,
    residualStandardDeviation: typeof result.diagnostics.residual_standard_deviation === "number" ? result.diagnostics.residual_standard_deviation : null,
    responseName: typeof result.diagnostics.response_name === "string" ? result.diagnostics.response_name : "Response",
  };
}

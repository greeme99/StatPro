import type { ResultBundle } from "./types";

export type ProcessPoint = { index: number; value: number; signal: boolean; rules: string[] };

type RuleSignal = {
  rule?: unknown;
  involved_indices?: unknown;
};

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
  const ruleSignals = result.plots.individuals?.rule_signals;
  const limits = result.tables.limits?.individuals;
  if (!Array.isArray(values) || !Array.isArray(signals) || !limits) return null;
  if (![limits.center, limits.ucl, limits.lcl].every(Number.isFinite)) return null;

  const signalIndices = new Set<number>(signals);
  const rulesByIndex = new Map<number, Set<string>>();
  if (Array.isArray(ruleSignals)) {
    for (const event of ruleSignals as RuleSignal[]) {
      if (typeof event?.rule !== "string" || !Array.isArray(event.involved_indices)) continue;
      for (const index of event.involved_indices) {
        if (typeof index !== "number" || !Number.isInteger(index) || index < 0) continue;
        const rules = rulesByIndex.get(index) ?? new Set<string>();
        rules.add(event.rule);
        rulesByIndex.set(index, rules);
      }
    }
  }
  const points = values
    .filter((value: unknown): value is number => typeof value === "number" && Number.isFinite(value))
    .map((value: number, zeroBasedIndex: number) => ({
      index: zeroBasedIndex + 1,
      value,
      signal: signalIndices.has(zeroBasedIndex),
      rules: [...(rulesByIndex.get(zeroBasedIndex) ?? [])].sort(),
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

export type DoePrediction = {
  point: number;
  actual: Record<string, number>;
  coded: Record<string, number>;
  predicted_response: number;
};

export type DoeOptimization = {
  goal: "maximize" | "minimize";
  standard_order: number;
  actual: Record<string, number>;
  coded: Record<string, number>;
  predicted_response: number;
  candidate_count: number;
};

export type DoeView = {
  coefficients: DoeCoefficient[];
  anova: DoeAnovaRow[];
  residuals: DoeResidual[];
  predictions: DoePrediction[];
  optimization: DoeOptimization[];
  rSquared: number | null;
  adjustedRSquared: number | null;
  residualStandardDeviation: number | null;
  responseName: string;
};

export type DoeDesirabilitySolution = {
  solution: number;
  actual: Record<string, number>;
  coded: Record<string, number>;
  composite_desirability: number;
  candidate_evaluations: number;
  search_method: string;
};

export type DoeResponseDesirability = {
  response: string;
  goal: "maximize" | "minimize" | "target";
  prediction: number;
  desirability: number;
  lower: number | null;
  target: number;
  upper: number | null;
  weight: number;
  importance: number;
};

export type DoeDesirabilityView = {
  solution: DoeDesirabilitySolution;
  responses: DoeResponseDesirability[];
  globalOptimumProven: boolean;
};

export type DoeFractionalDesignRow = {
  run_order: number;
  standard_order: number;
  replicate: number;
  coded: Record<string, number>;
  actual: Record<string, number>;
};

export type DoeAliasRow = {
  effect: string;
  alias_set: string[];
};

export type DoeFractionalView = {
  design: DoeFractionalDesignRow[];
  mainEffectAliases: DoeAliasRow[];
  twoFactorAliases: DoeAliasRow[];
  definingRelation: string;
  resolution: number;
  resolutionLabel: string;
  fraction: string;
  designNotation: string;
};

export function toDoeView(result: ResultBundle | undefined): DoeView | null {
  if (!result || result.analysis_type !== "doe.full_factorial_2level_analysis") return null;
  const coefficients = result.tables.coefficients;
  const anova = result.tables.anova;
  const residuals = result.tables.residuals;
  const predictions = result.tables.predictions ?? [];
  const optimization = result.tables.optimization ?? [];
  if (!Array.isArray(coefficients) || !Array.isArray(anova) || !Array.isArray(residuals) || !Array.isArray(predictions) || !Array.isArray(optimization)) return null;
  return {
    coefficients: coefficients as DoeCoefficient[],
    anova: anova as DoeAnovaRow[],
    residuals: residuals as DoeResidual[],
    predictions: predictions as DoePrediction[],
    optimization: optimization as DoeOptimization[],
    rSquared: typeof result.diagnostics.r_squared === "number" ? result.diagnostics.r_squared : null,
    adjustedRSquared: typeof result.diagnostics.adjusted_r_squared === "number" ? result.diagnostics.adjusted_r_squared : null,
    residualStandardDeviation: typeof result.diagnostics.residual_standard_deviation === "number" ? result.diagnostics.residual_standard_deviation : null,
    responseName: typeof result.diagnostics.response_name === "string" ? result.diagnostics.response_name : "Response",
  };
}

export function toDoeDesirabilityView(result: ResultBundle | undefined): DoeDesirabilityView | null {
  if (!result || result.analysis_type !== "doe.full_factorial_2level_desirability") return null;
  const solutions = result.tables.solution;
  const responses = result.tables.response_desirabilities;
  if (!Array.isArray(solutions) || solutions.length !== 1 || !Array.isArray(responses)) return null;
  return {
    solution: solutions[0] as DoeDesirabilitySolution,
    responses: responses as DoeResponseDesirability[],
    globalOptimumProven: result.diagnostics.global_optimum_proven === true,
  };
}

export function toDoeFractionalView(result: ResultBundle | undefined): DoeFractionalView | null {
  if (!result || result.analysis_type !== "doe.fractional_factorial_2level") return null;
  const design = result.tables.design;
  const mainEffectAliases = result.tables.main_effect_aliases;
  const twoFactorAliases = result.tables.two_factor_aliases;
  const relation = result.tables.defining_relation;
  if (!Array.isArray(design) || !Array.isArray(mainEffectAliases) || !Array.isArray(twoFactorAliases) || !Array.isArray(relation) || relation.length !== 1) return null;
  return {
    design: design as DoeFractionalDesignRow[],
    mainEffectAliases: mainEffectAliases as DoeAliasRow[],
    twoFactorAliases: twoFactorAliases as DoeAliasRow[],
    definingRelation: String(relation[0].expression ?? "I"),
    resolution: Number(result.diagnostics.resolution ?? 0),
    resolutionLabel: String(result.diagnostics.resolution_label ?? "—"),
    fraction: String(result.diagnostics.fraction ?? "—"),
    designNotation: String(result.diagnostics.design_notation ?? "—"),
  };
}

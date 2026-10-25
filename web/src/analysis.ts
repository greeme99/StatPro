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
  fraction_phase?: "original" | "foldover";
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

export type DoeFractionalAnalysisEffect = DoeScreeningEffect & {
  alias_set: string[];
  clear_of_two_factor_interactions: boolean;
  absolute_effect: number;
  display_value: number;
};

export type DoeFractionalAnalysisView = {
  effects: DoeFractionalAnalysisEffect[];
  rankedEffects: DoeFractionalAnalysisEffect[];
  responseName: string;
  inferenceMethod: string;
  referenceLine: number | null;
  residualDegreesOfFreedom: number;
  rSquared: number | null;
  foldover: boolean;
  resolutionLabel: string;
  augmentedResolution: number;
  mainEffectsClear: boolean;
};

export type DoeCentralCompositeRow = {
  run_order: number;
  standard_order: number | null;
  replicate: number;
  point_type: "factorial" | "axial" | "center";
  coded: Record<string, number>;
  actual: Record<string, number>;
};

export type DoeBoxBehnkenRow = {
  run_order: number;
  standard_order: number | null;
  replicate: number;
  block: number | null;
  point_type: "edge_midpoint" | "center";
  coded: Record<string, number>;
  actual: Record<string, number>;
};

export type DoeBoxBehnkenView = {
  design: DoeBoxBehnkenRow[];
  factorCount: number;
  edgeBlocks: number;
  edgePoints: number;
  centerPoints: number;
  quadraticModelEstimable: boolean;
};

export type DoeCentralCompositeView = {
  design: DoeCentralCompositeRow[];
  alpha: number;
  rotatable: boolean;
  factorialRuns: number;
  axialRuns: number;
  centerPoints: number;
};

export type DoeCentralCompositeAnalysisView = {
  coefficients: Array<{ term: string; kind: string; coefficient: number; standard_error: number | null; t_value: number | null; p_value: number | null; significant: boolean }>;
  anova: DoeAnovaRow[];
  residuals: DoeResidual[];
  responseName: string;
  alpha: number;
  rotatable: boolean;
  rSquared: number | null;
  adjustedRSquared: number | null;
  residualDegreesOfFreedom: number;
  lackOfFitDegreesOfFreedom: number;
};

export type DoeStationaryPoint = {
  classification: "minimum" | "maximum" | "saddle" | "ridge";
  available: boolean;
  coded: Record<string, number> | null;
  actual: Record<string, number> | null;
  predicted_response: number | null;
  inside_factorial_cube: boolean | null;
};

export type DoeSurfaceGridPoint = {
  x_index: number;
  y_index: number;
  x_coded: number;
  y_coded: number;
  x_actual: number;
  y_actual: number;
  predicted_response: number;
};

export type DoeContourSegment = {
  level: number;
  x1_coded: number;
  y1_coded: number;
  x2_coded: number;
  y2_coded: number;
  x1_actual: number;
  y1_actual: number;
  x2_actual: number;
  y2_actual: number;
};

export type DoeCentralCompositeSurfaceView = {
  stationary: DoeStationaryPoint;
  canonicalAxes: Array<{ axis: number; eigenvalue: number }>;
  grid: DoeSurfaceGridPoint[];
  extrema: Array<DoeSurfaceGridPoint & { kind: "minimum" | "maximum" }>;
  contours: DoeContourSegment[];
  responseName: string;
  plotFactors: string[];
  gridSize: number;
  contourLevels: number;
};

export type DoeScreeningDesignRow = {
  run_order: number;
  standard_order: number | null;
  replicate: number;
  point_type: string;
  coded: Record<string, number>;
  actual: Record<string, number>;
};

export type DoePlackettBurmanView = {
  design: DoeScreeningDesignRow[];
  factorCount: number;
  baseRunCount: number;
  totalRunCount: number;
  unusedFactorColumns: number;
  resolutionLabel: string;
  balanced: boolean;
  pairwiseOrthogonal: boolean;
  construction: string;
};

export type DoeScreeningEffect = {
  term: string;
  coefficient: number;
  effect: number;
  standard_error: number | null;
  standardized_effect: number | null;
  p_value: number | null;
  significant: boolean;
};

export type DoeConfirmationCandidate = {
  factor: string;
  effect: number;
  direction_for_increase: "high" | "low";
  suggested_level: number;
  opposite_level: number;
  selection_method: string;
};

export type DoePlackettBurmanAnalysisView = {
  effects: DoeScreeningEffect[];
  rankedEffects: Array<DoeScreeningEffect & { absolute_effect: number; display_value: number }>;
  confirmationCandidates: DoeConfirmationCandidate[];
  curvature: Array<{ factorial_mean: number; center_mean: number; difference: number; center_point_count: number }>;
  responseName: string;
  inferenceMethod: string;
  referenceLine: number | null;
  residualDegreesOfFreedom: number;
  rSquared: number | null;
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

export function toDoeFractionalAnalysisView(result: ResultBundle | undefined): DoeFractionalAnalysisView | null {
  if (!result || result.analysis_type !== "doe.fractional_factorial_2level_analysis") return null;
  const effects = result.tables.coefficients;
  const rankedEffects = result.tables.ranked_effects;
  if (!Array.isArray(effects) || !Array.isArray(rankedEffects)) return null;
  return {
    effects: effects as DoeFractionalAnalysisEffect[],
    rankedEffects: rankedEffects as DoeFractionalAnalysisEffect[],
    responseName: String(result.diagnostics.response_name ?? "Response"),
    inferenceMethod: String(result.diagnostics.inference_method ?? "unknown"),
    referenceLine: typeof result.diagnostics.pareto_reference_line === "number" ? result.diagnostics.pareto_reference_line : null,
    residualDegreesOfFreedom: Number(result.diagnostics.residual_degrees_of_freedom ?? 0),
    rSquared: typeof result.diagnostics.r_squared === "number" ? result.diagnostics.r_squared : null,
    foldover: result.parameters.foldover === true,
    resolutionLabel: String(result.diagnostics.resolution_label ?? "—"),
    augmentedResolution: Number(result.diagnostics.augmented_resolution ?? result.diagnostics.resolution ?? 0),
    mainEffectsClear: result.diagnostics.main_effects_clear_of_two_factor_interactions === true,
  };
}

export function toDoeCentralCompositeView(result: ResultBundle | undefined): DoeCentralCompositeView | null {
  if (!result || result.analysis_type !== "doe.central_composite") return null;
  const design = result.tables.design;
  if (!Array.isArray(design)) return null;
  return {
    design: design as DoeCentralCompositeRow[],
    alpha: Number(result.diagnostics.alpha ?? 0),
    rotatable: result.diagnostics.rotatable === true,
    factorialRuns: Number(result.diagnostics.factorial_run_count ?? 0),
    axialRuns: Number(result.diagnostics.axial_run_count ?? 0),
    centerPoints: Number(result.diagnostics.center_point_count ?? 0),
  };
}

export function toDoeBoxBehnkenView(result: ResultBundle | undefined): DoeBoxBehnkenView | null {
  if (!result || result.analysis_type !== "doe.box_behnken") return null;
  const design = result.tables.design;
  if (!Array.isArray(design)) return null;
  return {
    design: design as DoeBoxBehnkenRow[],
    factorCount: Number(result.diagnostics.factor_count ?? 0),
    edgeBlocks: Number(result.diagnostics.edge_block_count ?? 0),
    edgePoints: Number(result.diagnostics.edge_point_count ?? 0),
    centerPoints: Number(result.diagnostics.center_point_count ?? 0),
    quadraticModelEstimable: result.diagnostics.quadratic_model_estimable === true,
  };
}

export function toDoeCentralCompositeAnalysisView(result: ResultBundle | undefined): DoeCentralCompositeAnalysisView | null {
  if (!result || result.analysis_type !== "doe.central_composite_analysis") return null;
  const coefficients = result.tables.coefficients;
  const anova = result.tables.anova;
  const residuals = result.tables.residuals;
  if (!Array.isArray(coefficients) || !Array.isArray(anova) || !Array.isArray(residuals)) return null;
  return {
    coefficients: coefficients as DoeCentralCompositeAnalysisView["coefficients"],
    anova: anova as DoeAnovaRow[],
    residuals: residuals as DoeResidual[],
    responseName: String(result.diagnostics.response_name ?? "Response"),
    alpha: Number(result.diagnostics.alpha ?? 0),
    rotatable: result.diagnostics.rotatable === true,
    rSquared: typeof result.diagnostics.r_squared === "number" ? result.diagnostics.r_squared : null,
    adjustedRSquared: typeof result.diagnostics.adjusted_r_squared === "number" ? result.diagnostics.adjusted_r_squared : null,
    residualDegreesOfFreedom: Number(result.diagnostics.residual_degrees_of_freedom ?? 0),
    lackOfFitDegreesOfFreedom: Number(result.diagnostics.lack_of_fit_degrees_of_freedom ?? 0),
  };
}

export function toDoeCentralCompositeSurfaceView(result: ResultBundle | undefined): DoeCentralCompositeSurfaceView | null {
  if (!result || result.analysis_type !== "doe.central_composite_surface") return null;
  const stationary = result.tables.stationary_point;
  const canonicalAxes = result.tables.canonical_axes;
  const grid = result.tables.surface_grid;
  const extrema = result.tables.surface_slice_extrema;
  const contours = result.tables.surface_contours;
  const plotFactors = result.diagnostics.plot_factors;
  if (!Array.isArray(stationary) || stationary.length !== 1 || !Array.isArray(canonicalAxes) || !Array.isArray(grid) || !Array.isArray(extrema) || !Array.isArray(contours) || !Array.isArray(plotFactors) || plotFactors.length !== 2) return null;
  return {
    stationary: stationary[0] as DoeStationaryPoint,
    canonicalAxes: canonicalAxes as DoeCentralCompositeSurfaceView["canonicalAxes"],
    grid: grid as DoeSurfaceGridPoint[],
    extrema: extrema as DoeCentralCompositeSurfaceView["extrema"],
    contours: contours as DoeContourSegment[],
    responseName: String(result.diagnostics.response_name ?? "Response"),
    plotFactors: plotFactors.map(String),
    gridSize: Number(result.diagnostics.surface_grid_size ?? 0),
    contourLevels: Number(result.diagnostics.contour_level_count ?? 0),
  };
}

export function toDoePlackettBurmanView(result: ResultBundle | undefined): DoePlackettBurmanView | null {
  if (!result || result.analysis_type !== "doe.plackett_burman") return null;
  const design = result.tables.design;
  if (!Array.isArray(design)) return null;
  return {
    design: design as DoeScreeningDesignRow[],
    factorCount: Number(result.diagnostics.factor_count ?? 0),
    baseRunCount: Number(result.diagnostics.base_run_count ?? 0),
    totalRunCount: Number(result.diagnostics.total_run_count ?? 0),
    unusedFactorColumns: Number(result.diagnostics.unused_factor_columns ?? 0),
    resolutionLabel: String(result.diagnostics.resolution_label ?? "—"),
    balanced: result.diagnostics.balanced === true,
    pairwiseOrthogonal: result.diagnostics.pairwise_orthogonal === true,
    construction: String(result.diagnostics.construction ?? "unknown"),
  };
}

export function toDoePlackettBurmanAnalysisView(result: ResultBundle | undefined): DoePlackettBurmanAnalysisView | null {
  if (!result || result.analysis_type !== "doe.plackett_burman_analysis") return null;
  const effects = result.tables.coefficients;
  const rankedEffects = result.tables.ranked_effects;
  const confirmationCandidates = result.tables.confirmation_candidates;
  const curvature = result.tables.curvature ?? [];
  if (!Array.isArray(effects) || !Array.isArray(rankedEffects) || !Array.isArray(confirmationCandidates) || !Array.isArray(curvature)) return null;
  return {
    effects: effects as DoeScreeningEffect[],
    rankedEffects: rankedEffects as Array<DoeScreeningEffect & { absolute_effect: number; display_value: number }>,
    confirmationCandidates: confirmationCandidates as DoeConfirmationCandidate[],
    curvature: curvature as Array<{ factorial_mean: number; center_mean: number; difference: number; center_point_count: number }>,
    responseName: String(result.diagnostics.response_name ?? "Response"),
    inferenceMethod: String(result.diagnostics.inference_method ?? "unknown"),
    referenceLine: typeof result.diagnostics.pareto_reference_line === "number" ? result.diagnostics.pareto_reference_line : null,
    residualDegreesOfFreedom: Number(result.diagnostics.residual_degrees_of_freedom ?? 0),
    rSquared: typeof result.diagnostics.r_squared === "number" ? result.diagnostics.r_squared : null,
  };
}

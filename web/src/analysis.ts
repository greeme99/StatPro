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
  movingRangePoints?: ProcessPoint[];
  movingRange?: { center: number; ucl: number; lcl: number };
};

export function toImrView(result: ResultBundle | undefined): ImrView | null {
  if (!result || result.analysis_type !== "spc.imr") return null;

  const values = result.plots.individuals?.values;
  const signals = result.plots.individuals?.signals;
  const ruleSignals = result.plots.individuals?.rule_signals;
  const limits = result.tables.limits?.individuals;
  const movingRangeValues = result.plots.moving_range?.values;
  const movingRangeSignals = result.plots.moving_range?.signals;
  const movingRangeLimits = result.tables.limits?.moving_range;
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
  const hasMovingRange = Array.isArray(movingRangeValues) && Array.isArray(movingRangeSignals) && movingRangeLimits
    && [movingRangeLimits.center, movingRangeLimits.ucl, movingRangeLimits.lcl].every(Number.isFinite);
  if (hasMovingRange && (
    movingRangeValues.some((value) => typeof value !== "number" || !Number.isFinite(value))
    || movingRangeSignals.some((value) => typeof value !== "number" || !Number.isInteger(value) || value < 1 || value > movingRangeValues.length)
  )) return null;
  const movingRangeSignalSet = new Set(hasMovingRange ? movingRangeSignals as number[] : []);
  const movingRangePoints = hasMovingRange ? (movingRangeValues as number[]).map((value, zeroBasedIndex) => ({
    index: zeroBasedIndex + 1,
    value,
    signal: movingRangeSignalSet.has(zeroBasedIndex + 1),
    rules: [],
  })) : undefined;

  return {
    points,
    center: limits.center,
    ucl: limits.ucl,
    lcl: limits.lcl,
    movingRangePoints,
    movingRange: hasMovingRange ? movingRangeLimits : undefined,
  };
}

export type XbarSView = {
  subgroupSize: number;
  estimatedSigma: number;
  xbarPoints: ProcessPoint[];
  sPoints: ProcessPoint[];
  xbarLimits: { center: number; ucl: number; lcl: number };
  sLimits: { center: number; ucl: number; lcl: number };
};

export type XbarRView = {
  subgroupSize: number;
  xbarPoints: ProcessPoint[];
  rangePoints: ProcessPoint[];
  xbarLimits: { center: number; ucl: number; lcl: number };
  rangeLimits: { center: number; ucl: number; lcl: number };
};

export function toXbarRView(result: ResultBundle | undefined): XbarRView | null {
  if (!result || result.analysis_type !== "spc.xbar_r") return null;
  const xbarValues = result.plots.xbar?.values;
  const xbarSignals = result.plots.xbar?.signals;
  const rangeValues = result.plots.range?.values;
  const rangeSignals = result.plots.range?.signals;
  const xbarLimits = result.tables.limits?.xbar;
  const rangeLimits = result.tables.limits?.range;
  const subgroupSize = result.parameters.subgroup_size;
  if (
    !Array.isArray(xbarValues) || !Array.isArray(xbarSignals) || !Array.isArray(rangeValues) || !Array.isArray(rangeSignals)
    || !xbarLimits || !rangeLimits || typeof subgroupSize !== "number" || !Number.isInteger(subgroupSize) || subgroupSize < 2 || subgroupSize > 10
    || ![xbarLimits.center, xbarLimits.ucl, xbarLimits.lcl, rangeLimits.center, rangeLimits.ucl, rangeLimits.lcl].every(Number.isFinite)
    || xbarValues.length !== rangeValues.length
    || xbarValues.some((value) => typeof value !== "number" || !Number.isFinite(value))
    || rangeValues.some((value) => typeof value !== "number" || !Number.isFinite(value))
    || xbarSignals.some((value) => typeof value !== "number" || !Number.isInteger(value) || value < 0 || value >= xbarValues.length)
    || rangeSignals.some((value) => typeof value !== "number" || !Number.isInteger(value) || value < 0 || value >= rangeValues.length)
  ) return null;
  const points = (values: unknown[], signals: unknown[]) => {
    const signalSet = new Set(signals as number[]);
    return (values as number[]).map((value, index) => ({ index: index + 1, value, signal: signalSet.has(index), rules: [] }));
  };
  return {
    subgroupSize,
    xbarPoints: points(xbarValues, xbarSignals),
    rangePoints: points(rangeValues, rangeSignals),
    xbarLimits,
    rangeLimits,
  };
}

export function toXbarSView(result: ResultBundle | undefined): XbarSView | null {
  if (!result || result.analysis_type !== "spc.xbar_s") return null;
  const xbarValues = result.plots.xbar?.values;
  const xbarSignals = result.plots.xbar?.signals;
  const sValues = result.plots.standard_deviation?.values;
  const sSignals = result.plots.standard_deviation?.signals;
  const xbarLimits = result.tables.limits?.xbar;
  const sLimits = result.tables.limits?.standard_deviation;
  if (!Array.isArray(xbarValues) || !Array.isArray(xbarSignals) || !Array.isArray(sValues) || !Array.isArray(sSignals) || !xbarLimits || !sLimits) return null;
  if (![xbarLimits.center, xbarLimits.ucl, xbarLimits.lcl, sLimits.center, sLimits.ucl, sLimits.lcl].every(Number.isFinite)) return null;
  const subgroupSize = result.parameters.subgroup_size;
  const estimatedSigma = result.diagnostics.estimated_sigma;
  if (
    typeof subgroupSize !== "number" || !Number.isInteger(subgroupSize) || subgroupSize < 2
    || typeof estimatedSigma !== "number" || !Number.isFinite(estimatedSigma) || estimatedSigma < 0
    || xbarValues.length !== sValues.length
    || xbarValues.some((value) => typeof value !== "number" || !Number.isFinite(value))
    || sValues.some((value) => typeof value !== "number" || !Number.isFinite(value))
    || xbarSignals.some((value) => typeof value !== "number" || !Number.isInteger(value) || value < 0 || value >= xbarValues.length)
    || sSignals.some((value) => typeof value !== "number" || !Number.isInteger(value) || value < 0 || value >= sValues.length)
  ) return null;
  const points = (values: unknown[], signals: unknown[]) => {
    const signalSet = new Set(signals as number[]);
    return (values as number[]).map((value, index) => ({ index: index + 1, value, signal: signalSet.has(index), rules: [] }));
  };
  return {
    subgroupSize,
    estimatedSigma,
    xbarPoints: points(xbarValues, xbarSignals),
    sPoints: points(sValues, sSignals),
    xbarLimits,
    sLimits,
  };
}

export type EwmaPoint = {
  index: number;
  observation: number;
  ewma: number;
  center: number;
  ucl: number;
  lcl: number;
  signal: boolean;
};

export type EwmaView = {
  points: EwmaPoint[];
  weight: number;
  limitWidth: number;
  processSigma: number;
  meanSource: string;
  sigmaSource: string;
};

export function toEwmaView(result: ResultBundle | undefined): EwmaView | null {
  if (!result || result.analysis_type !== "spc.ewma") return null;
  const rows = result.tables.chart_points;
  if (!Array.isArray(rows)) return null;
  const points: EwmaPoint[] = [];
  for (const row of rows) {
    if (
      typeof row !== "object" || row === null
      || !["index", "observation", "ewma", "center", "ucl", "lcl"].every(
        (key) => typeof row[key] === "number" && Number.isFinite(row[key]),
      )
      || typeof row.signal !== "boolean"
    ) return null;
    points.push({
      index: row.index + 1,
      observation: row.observation,
      ewma: row.ewma,
      center: row.center,
      ucl: row.ucl,
      lcl: row.lcl,
      signal: row.signal,
    });
  }
  const weight = result.parameters.weight;
  const limitWidth = result.parameters.limit_width;
  const processSigma = result.parameters.process_sigma;
  const meanSource = result.parameters.mean_source;
  const sigmaSource = result.parameters.sigma_source;
  if (
    typeof weight !== "number" || !Number.isFinite(weight)
    || typeof limitWidth !== "number" || !Number.isFinite(limitWidth)
    || typeof processSigma !== "number" || !Number.isFinite(processSigma)
    || typeof meanSource !== "string" || typeof sigmaSource !== "string"
  ) return null;
  return { points, weight, limitWidth, processSigma, meanSource, sigmaSource };
}

export type CusumPoint = {
  index: number;
  observation: number;
  upperCusum: number;
  lowerCusum: number;
  center: number;
  ucl: number;
  lcl: number;
  signal: boolean;
  signalDirection: "upper" | "lower" | "both" | null;
};

export type CusumView = {
  points: CusumPoint[];
  referenceValue: number;
  decisionInterval: number;
  processSigma: number;
  meanSource: string;
  sigmaSource: string;
};

export function toCusumView(result: ResultBundle | undefined): CusumView | null {
  if (!result || result.analysis_type !== "spc.cusum") return null;
  const rows = result.tables.chart_points;
  if (!Array.isArray(rows)) return null;
  const points: CusumPoint[] = [];
  for (const row of rows) {
    if (
      typeof row !== "object" || row === null
      || !["index", "observation", "upper_cusum", "lower_cusum", "center", "ucl", "lcl"].every(
        (key) => typeof row[key] === "number" && Number.isFinite(row[key]),
      )
      || typeof row.signal !== "boolean"
      || (row.signal_direction !== null && !["upper", "lower", "both"].includes(String(row.signal_direction)))
    ) return null;
    points.push({
      index: row.index + 1,
      observation: row.observation,
      upperCusum: row.upper_cusum,
      lowerCusum: row.lower_cusum,
      center: row.center,
      ucl: row.ucl,
      lcl: row.lcl,
      signal: row.signal,
      signalDirection: row.signal_direction as CusumPoint["signalDirection"],
    });
  }
  const referenceValue = result.parameters.reference_value;
  const decisionInterval = result.parameters.decision_interval;
  const processSigma = result.parameters.process_sigma;
  const meanSource = result.parameters.mean_source;
  const sigmaSource = result.parameters.sigma_source;
  if (
    typeof referenceValue !== "number" || !Number.isFinite(referenceValue)
    || typeof decisionInterval !== "number" || !Number.isFinite(decisionInterval)
    || typeof processSigma !== "number" || !Number.isFinite(processSigma)
    || typeof meanSource !== "string" || typeof sigmaSource !== "string"
  ) return null;
  return { points, referenceValue, decisionInterval, processSigma, meanSource, sigmaSource };
}

export type AttributeChartPoint = {
  index: number;
  eventCount: number;
  opportunity: number;
  statistic: number;
  center: number;
  ucl: number;
  lcl: number;
  signal: boolean;
};

export type RareEventChartPoint = {
  index: number;
  interval: number;
  center: number;
  ucl: number;
  lcl: number;
  signal: boolean;
};

export type RareEventChartView = {
  chart: "g" | "t";
  distribution: "geometric" | "exponential";
  points: RareEventChartPoint[];
  meanInterval: number;
  observedMeanInterval: number;
  parameterSource: "phase_1_estimated" | "phase_2_historical";
  signalCount: number;
};

export function toRareEventChartView(
  result: ResultBundle | undefined,
): RareEventChartView | null {
  if (!result || !["spc.g_chart", "spc.t_chart"].includes(result.analysis_type)) return null;
  const rows = result.tables.chart_points;
  const summary = result.tables.summary;
  const distribution = result.parameters.distribution;
  if (!Array.isArray(rows) || !summary || (distribution !== "geometric" && distribution !== "exponential")) return null;
  const points: RareEventChartPoint[] = [];
  for (const row of rows) {
    if (
      typeof row !== "object" || row === null
      || !["index", "interval", "center", "ucl", "lcl"].every(
        (key) => typeof row[key] === "number" && Number.isFinite(row[key]),
      )
      || typeof row.signal !== "boolean"
    ) return null;
    points.push({
      index: row.index + 1,
      interval: row.interval,
      center: row.center,
      ucl: row.ucl,
      lcl: row.lcl,
      signal: row.signal,
    });
  }
  const parameterSource = result.parameters.parameter_source === "phase_2_historical"
    ? "phase_2_historical"
    : "phase_1_estimated";
  const observedMeanInterval = typeof summary.observed_mean_interval === "number"
    && Number.isFinite(summary.observed_mean_interval)
    ? summary.observed_mean_interval
    : summary.mean_interval;
  if (
    typeof summary.mean_interval !== "number" || !Number.isFinite(summary.mean_interval)
    || typeof observedMeanInterval !== "number" || !Number.isFinite(observedMeanInterval)
  ) return null;
  return {
    chart: result.analysis_type === "spc.g_chart" ? "g" : "t",
    distribution,
    points,
    meanInterval: summary.mean_interval,
    observedMeanInterval,
    parameterSource,
    signalCount: points.filter((point) => point.signal).length,
  };
}

export type AttributeChartView = {
  chart: "p" | "np" | "c" | "u" | "p_prime" | "u_prime";
  points: AttributeChartPoint[];
  pooledRate: number;
  totalEvents: number;
  totalOpportunity: number;
  signalCount: number;
};

export function toAttributeChartView(
  result: ResultBundle | undefined,
): AttributeChartView | null {
  if (!result || !["spc.p_chart", "spc.np_chart", "spc.c_chart", "spc.u_chart", "spc.laney_p_prime", "spc.laney_u_prime"].includes(result.analysis_type)) return null;
  const rows = result.tables.chart_points;
  const summary = result.tables.summary;
  if (!Array.isArray(rows) || !summary) return null;

  const points: AttributeChartPoint[] = [];
  for (const row of rows) {
    if (
      typeof row !== "object" || row === null
      || !["index", "event_count", "opportunity", "statistic", "center", "ucl", "lcl"].every(
        (key) => typeof row[key] === "number" && Number.isFinite(row[key]),
      )
      || typeof row.signal !== "boolean"
    ) return null;
    points.push({
      index: row.index + 1,
      eventCount: row.event_count,
      opportunity: row.opportunity,
      statistic: row.statistic,
      center: row.center,
      ucl: row.ucl,
      lcl: row.lcl,
      signal: row.signal,
    });
  }
  if (
    typeof (summary.pooled_proportion ?? summary.average_defects_per_unit ?? summary.pooled_rate) !== "number"
    || typeof (summary.total_nonconforming ?? summary.total_defects ?? summary.total_events) !== "number"
    || typeof (summary.total_inspected ?? summary.total_inspection_units ?? summary.total_opportunity) !== "number"
  ) return null;
  const chart = result.analysis_type.startsWith("spc.laney_")
    ? result.analysis_type.replace("spc.laney_", "") as "p_prime" | "u_prime"
    : result.analysis_type.replace("spc.", "").replace("_chart", "") as "p" | "np" | "c" | "u";
  return {
    chart,
    points,
    pooledRate: summary.pooled_proportion ?? summary.average_defects_per_unit ?? summary.pooled_rate,
    totalEvents: summary.total_nonconforming ?? summary.total_defects ?? summary.total_events,
    totalOpportunity: summary.total_inspected ?? summary.total_inspection_units ?? summary.total_opportunity,
    signalCount: points.filter((point) => point.signal).length,
  };
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
  block: number;
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
  blockGenerators: Array<{ contrast: string; terms: string[]; expression: string }>;
  blockAliases: Array<{ contrast: string; generator_terms: string; treatment_alias_set: string[] }>;
  blockEffects: Array<{ contrast: string; coefficient: number; effect: number; generator_terms: string; treatment_alias_set: string[] }>;
  confoundedTerms: Array<{ term: string; reason: string }>;
  blockCount: number;
  blockedResolutionLabel: string | null;
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
  factorConstraints: Record<string, { lower: number; upper: number }>;
  globalOptimumProven: boolean;
};

export type DoeFractionalDesignRow = {
  run_order: number;
  standard_order: number;
  replicate: number;
  block?: number;
  fraction_phase?: "original" | "foldover";
  coded: Record<string, number>;
  actual: Record<string, number>;
};

export type DoeAliasRow = {
  effect: string;
  alias_set: string[];
  clear_of_two_factor_interactions?: boolean;
};

export type DoeFractionalView = {
  design: DoeFractionalDesignRow[];
  generators: Array<{ factor: string; terms: string[]; expression: string }>;
  blockGenerators: Array<{ contrast: string; terms: string[]; expression: string }>;
  blockAliases: Array<{ contrast: string; generator_terms: string; treatment_alias_set: string[] }>;
  mainEffectAliases: DoeAliasRow[];
  twoFactorAliases: DoeAliasRow[];
  definingRelation: string;
  resolution: number;
  resolutionLabel: string;
  fraction: string;
  designNotation: string;
  automaticSelection: boolean;
  selectionObjective: string | null;
  candidateSetsExamined: number | null;
  wordLengthPattern: Record<string, number>;
  blockCount: number;
  blockedResolutionLabel: string | null;
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
  foldoverMode: "none" | "all_factors" | "single_factor";
  foldoverFactor: string | null;
  clearedMainEffects: string[];
  resolutionLabel: string;
  augmentedResolution: number;
  mainEffectsClear: boolean;
  blockEffects: Array<{ contrast: string; coefficient: number; effect: number; generator_terms: string; treatment_alias_set: string[] }>;
  blockCount: number;
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

export type DoeQuadraticAnalysisView = {
  coefficients: Array<{ term: string; kind: string; coefficient: number; standard_error: number | null; t_value: number | null; p_value: number | null; significant: boolean }>;
  anova: DoeAnovaRow[];
  residuals: DoeResidual[];
  responseName: string;
  alpha: number;
  rSquared: number | null;
  adjustedRSquared: number | null;
  residualDegreesOfFreedom: number;
  lackOfFitDegreesOfFreedom: number;
};

export type DoeCentralCompositeAnalysisView = DoeQuadraticAnalysisView & { rotatable: boolean };
export type DoeBoxBehnkenAnalysisView = DoeQuadraticAnalysisView;

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
    blockGenerators: Array.isArray(result.tables.block_generators) ? result.tables.block_generators as Array<{ contrast: string; terms: string[]; expression: string }> : [],
    blockAliases: Array.isArray(result.tables.block_aliases) ? result.tables.block_aliases as Array<{ contrast: string; generator_terms: string; treatment_alias_set: string[] }> : [],
    blockEffects: Array.isArray(result.tables.block_effects) ? result.tables.block_effects as Array<{ contrast: string; coefficient: number; effect: number; generator_terms: string; treatment_alias_set: string[] }> : [],
    confoundedTerms: Array.isArray(result.tables.confounded_terms) ? result.tables.confounded_terms as Array<{ term: string; reason: string }> : [],
    blockCount: Number(result.diagnostics.block_count ?? 1),
    blockedResolutionLabel: typeof result.diagnostics.blocked_resolution_label === "string" ? result.diagnostics.blocked_resolution_label : null,
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
    factorConstraints: result.parameters.factor_constraints && typeof result.parameters.factor_constraints === "object"
      ? result.parameters.factor_constraints as Record<string, { lower: number; upper: number }>
      : {},
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
    generators: Array.isArray(result.tables.generators) ? result.tables.generators as Array<{ factor: string; terms: string[]; expression: string }> : [],
    blockGenerators: Array.isArray(result.tables.block_generators) ? result.tables.block_generators as Array<{ contrast: string; terms: string[]; expression: string }> : [],
    blockAliases: Array.isArray(result.tables.block_aliases) ? result.tables.block_aliases as Array<{ contrast: string; generator_terms: string; treatment_alias_set: string[] }> : [],
    mainEffectAliases: mainEffectAliases as DoeAliasRow[],
    twoFactorAliases: twoFactorAliases as DoeAliasRow[],
    definingRelation: String(relation[0].expression ?? "I"),
    resolution: Number(result.diagnostics.resolution ?? 0),
    resolutionLabel: String(result.diagnostics.resolution_label ?? "—"),
    fraction: String(result.diagnostics.fraction ?? "—"),
    designNotation: String(result.diagnostics.design_notation ?? "—"),
    automaticSelection: result.diagnostics.generator_selection_mode === "automatic",
    selectionObjective: typeof result.diagnostics.selection_objective === "string" ? result.diagnostics.selection_objective : null,
    candidateSetsExamined: typeof result.diagnostics.candidate_sets_examined === "number" ? result.diagnostics.candidate_sets_examined : null,
    wordLengthPattern: typeof result.diagnostics.word_length_pattern === "object" && result.diagnostics.word_length_pattern !== null ? result.diagnostics.word_length_pattern as Record<string, number> : {},
    blockCount: Number(result.diagnostics.block_count ?? 1),
    blockedResolutionLabel: typeof result.diagnostics.blocked_resolution_label === "string" ? result.diagnostics.blocked_resolution_label : null,
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
    foldoverMode: ["all_factors", "single_factor"].includes(String(result.diagnostics.foldover_mode))
      ? result.diagnostics.foldover_mode as "all_factors" | "single_factor"
      : "none",
    foldoverFactor: typeof result.diagnostics.foldover_factor === "string" ? result.diagnostics.foldover_factor : null,
    clearedMainEffects: Array.isArray(result.diagnostics.cleared_main_effects)
      ? result.diagnostics.cleared_main_effects.map(String)
      : [],
    resolutionLabel: String(result.diagnostics.resolution_label ?? "—"),
    augmentedResolution: Number(result.diagnostics.augmented_resolution ?? result.diagnostics.resolution ?? 0),
    mainEffectsClear: result.diagnostics.main_effects_clear_of_two_factor_interactions === true,
    blockEffects: Array.isArray(result.tables.block_effects) ? result.tables.block_effects as Array<{ contrast: string; coefficient: number; effect: number; generator_terms: string; treatment_alias_set: string[] }> : [],
    blockCount: Number(result.diagnostics.block_count ?? 1),
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

export function toDoeBoxBehnkenAnalysisView(result: ResultBundle | undefined): DoeBoxBehnkenAnalysisView | null {
  if (!result || result.analysis_type !== "doe.box_behnken_analysis") return null;
  const coefficients = result.tables.coefficients;
  const anova = result.tables.anova;
  const residuals = result.tables.residuals;
  if (!Array.isArray(coefficients) || !Array.isArray(anova) || !Array.isArray(residuals)) return null;
  return {
    coefficients: coefficients as DoeBoxBehnkenAnalysisView["coefficients"],
    anova: anova as DoeAnovaRow[],
    residuals: residuals as DoeResidual[],
    responseName: String(result.diagnostics.response_name ?? "Response"),
    alpha: Number(result.diagnostics.alpha ?? 0),
    rSquared: typeof result.diagnostics.r_squared === "number" ? result.diagnostics.r_squared : null,
    adjustedRSquared: typeof result.diagnostics.adjusted_r_squared === "number" ? result.diagnostics.adjusted_r_squared : null,
    residualDegreesOfFreedom: Number(result.diagnostics.residual_degrees_of_freedom ?? 0),
    lackOfFitDegreesOfFreedom: Number(result.diagnostics.lack_of_fit_degrees_of_freedom ?? 0),
  };
}

export function toDoeCentralCompositeSurfaceView(result: ResultBundle | undefined): DoeCentralCompositeSurfaceView | null {
  if (!result || !["doe.central_composite_surface", "doe.box_behnken_surface"].includes(result.analysis_type)) return null;
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

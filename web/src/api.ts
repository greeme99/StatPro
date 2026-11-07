import type { ActionPriorityPolicyPage, ApiError, CellValue, DefectAnalysisPage, DmaicProjectPage, FmeaStudyPage, FmeaStudyReport, QualityMetricPage, StoredActionPriorityPolicy, StoredCheckSheet, StoredDefectAnalysis, StoredDmaicCharter, StoredDmaicControlHandoff, StoredDmaicMeasurementPlan, StoredDmaicPilotPlan, StoredDmaicProject, StoredDmaicRootCauseAnalysis, StoredDmaicSolutionSelection, StoredFishbone, StoredFmeaStudy, StoredQualityMetric, RunPage, StoredRun, StoredWorksheet, WorksheetPage } from "./types";

const API_BASE = import.meta.env.VITE_STATPRO_API_URL ?? "/api";

export type CopilotGuidanceResponse = {
  answer: string;
  provider: string;
  sources: Array<{ title: string; reference: string; evidence_kind: string }>;
  limitations: string[];
  action: { label: string; href: string } | null;
  guidance_mode: "rulebase" | "llm_fallback" | "unmatched";
  rule_id: string | null;
  recommended_tool: string | null;
  menu_path: string[];
  checklist: string[];
  workflow_steps: string[];
};

export type CopilotRule = {
  rule_id: string;
  domain: string;
  situation: string;
  recommended_tool: string;
  menu_path: string[];
  action: { label: string; href: string };
  checklist: string[];
  workflow_steps: string[];
  source_reference: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = await response.text();
  let payload: T | ApiError | undefined;

  if (body.trim()) {
    try {
      payload = JSON.parse(body) as T | ApiError;
    } catch {
      throw new Error("분석 서버의 응답 형식을 읽지 못했습니다. 로컬 분석 서버 로그를 확인하세요.");
    }
  }

  if (!response.ok) {
    const error = payload as ApiError | undefined;
    throw new Error(error?.error?.message ?? `요청을 완료하지 못했습니다. (HTTP ${response.status})`);
  }
  if (payload === undefined) {
    throw new Error("분석 실행 결과가 비어 있습니다. 로컬 분석 서버 로그를 확인하세요.");
  }
  return payload as T;
}

export function listRuns(limit = 20): Promise<RunPage> {
  return request(`/v1/analysis-runs?limit=${limit}`);
}

export function getHealth(): Promise<{ status: string; engine_version: string }> {
  return request("/health");
}

export async function getCopilotGuidance(payload: {
  question: string;
  pathname: string;
  workspace: string;
  evidence_context?: string | null;
}): Promise<CopilotGuidanceResponse> {
  const guidance = await request<CopilotGuidanceResponse>("/v1/copilot/guidance", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  if (
    typeof guidance.answer !== "string"
    || typeof guidance.provider !== "string"
    || !Array.isArray(guidance.sources)
    || !Array.isArray(guidance.limitations)
    || !["rulebase", "llm_fallback", "unmatched"].includes(guidance.guidance_mode)
    || !Array.isArray(guidance.menu_path)
    || !Array.isArray(guidance.checklist)
    || !Array.isArray(guidance.workflow_steps)
  ) {
    throw new Error("Copilot 응답 계약이 올바르지 않습니다.");
  }
  return guidance;
}

export function listCopilotRules(filters: { domain?: string; limit?: number } = {}): Promise<CopilotRule[]> {
  const params = new URLSearchParams();
  if (filters.domain) params.set("domain", filters.domain);
  if (filters.limit) params.set("limit", String(filters.limit));
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request(`/v1/copilot/rules${suffix}`);
}

export function getRun(runId: string): Promise<StoredRun> {
  return request(`/v1/analysis-runs/${encodeURIComponent(runId)}`);
}

export function listQualityMetrics(limit = 50): Promise<QualityMetricPage> {
  return request(`/v1/quality-metrics?limit=${limit}`);
}

export function createQualityMetric(payload: {
  metric_id: string;
  name: string;
  unit: string;
  run_id: string;
  value_path: string;
  refresh_cycle: string;
  owner_ref: string;
  lower_warning?: number | null;
  lower_critical?: number | null;
  upper_warning?: number | null;
  upper_critical?: number | null;
}): Promise<StoredQualityMetric> {
  return request("/v1/quality-metrics", { method: "POST", body: JSON.stringify(payload) });
}

export type DefectAnalysisPayload = {
  analysis_id?: string;
  title: string;
  process_name: string;
  period: string;
  owner_ref: string;
  source_check_sheet_id?: string | null;
  categories: Array<{ category: string; defect_count: number; opportunity_count: number; unit_loss: number; severity: number }>;
};

export function listDefectAnalyses(limit = 50): Promise<DefectAnalysisPage> {
  return request(`/v1/defect-analyses?limit=${limit}`);
}

export function createDefectAnalysis(payload: DefectAnalysisPayload & { analysis_id: string }): Promise<StoredDefectAnalysis> {
  return request("/v1/defect-analyses", { method: "POST", body: JSON.stringify(payload) });
}

export function reviseDefectAnalysis(analysisId: string, payload: DefectAnalysisPayload & { expected_storage_version: number }): Promise<StoredDefectAnalysis> {
  return request(`/v1/defect-analyses/${encodeURIComponent(analysisId)}`, { method: "PUT", body: JSON.stringify(payload) });
}

export function listDmaicProjects(limit = 50): Promise<DmaicProjectPage> {
  return request(`/v1/dmaic-projects?limit=${limit}`);
}

export function createDmaicProject(payload: {
  project_id: string;
  title: string;
  owner_ref: string;
  sponsor_ref?: string | null;
  champion_ref?: string | null;
  department?: string | null;
  start_date?: string | null;
  target_end_date?: string | null;
}): Promise<StoredDmaicProject> {
  return request("/v1/dmaic-projects", { method: "POST", body: JSON.stringify(payload) });
}

export function saveDmaicCharter(projectId: string, payload: {
  expected_storage_version: number;
  business_case: string;
  problem_statement: string;
  scope_in: string[];
  scope_out: string[];
  success_metrics: string[];
  team_refs: string[];
  budget?: string | null;
  milestones: string[];
  risk_refs: string[];
  assumptions_constraints: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/charters`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function saveDmaicVoiceOfCustomer(projectId: string, payload: {
  expected_storage_version: number;
  collection_plan: string;
  data_points: string[];
  requirements: string[];
  pain_points: string[];
  opportunities: string[];
  actions: string[];
  recommendations: string[];
  next_steps: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/voice-of-customer-studies`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function saveDmaicSipoc(projectId: string, payload: {
  expected_storage_version: number;
  process_start_boundary: string;
  process_end_boundary: string;
  suppliers: string[];
  inputs: string[];
  process_steps: string[];
  outputs: string[];
  customers: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/sipoc-maps`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function saveDmaicStakeholderAssessment(projectId: string, payload: {
  expected_storage_version: number;
  stakeholders: Array<{
    stakeholder_id: string;
    name: string;
    role: string;
    department?: string | null;
    influence: number;
    interest: number;
    attitude: "supportive" | "neutral" | "resistant";
    communication: "low" | "medium" | "high";
    concerns: string[];
    expectations: string[];
  }>;
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/stakeholder-assessments`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function saveDmaicProblemDefinition(projectId: string, payload: {
  expected_storage_version: number;
  problem_statement: string;
  impact: string;
  current_state: string;
  target_state: string;
  timeframe: string;
  location_scope: string;
  severity: "low" | "medium" | "high";
  urgency: "low" | "medium" | "high";
  objectives: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/problem-definitions`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function saveDmaicMeasurementPlan(projectId: string, payload: {
  expected_storage_version: number;
  primary_metric: string;
  baseline_value?: number | null;
  target_value?: number | null;
  data_source: string;
  collection_method: string;
  collection_frequency: string;
  sampling_method: string;
  population_size?: number | null;
  sample_size?: number | null;
  sampling_rationale?: string | null;
  measurement_instrument?: string | null;
  measurement_unit?: string | null;
  measurement_precision?: string | null;
  calibration_required: boolean;
  msa_required: boolean;
  analysis_run_ids: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/measurement-plans`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function getDmaicMeasurementPlan(projectId: string, documentId: string): Promise<StoredDmaicMeasurementPlan> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/measurement-plans/${encodeURIComponent(documentId)}`);
}

export function saveDmaicRootCauseAnalysis(projectId: string, payload: {
  expected_storage_version: number;
  problem_statement: string;
  method: "fishbone_pareto" | "five_whys" | "data_analysis";
  candidate_causes: string[];
  verified_causes: string[];
  next_actions: string[];
  analysis_run_ids: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/root-cause-analyses`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function getDmaicRootCauseAnalysis(projectId: string, documentId: string): Promise<StoredDmaicRootCauseAnalysis> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/root-cause-analyses/${encodeURIComponent(documentId)}`);
}

export function saveDmaicSolutionSelection(projectId: string, payload: {
  expected_storage_version: number;
  problem_statement: string;
  candidate_solutions: string[];
  selected_solution: string;
  decision_rationale: string;
  validation_plan: string;
  analysis_run_ids: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/solution-selections`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function getDmaicSolutionSelection(projectId: string, documentId: string): Promise<StoredDmaicSolutionSelection> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/solution-selections/${encodeURIComponent(documentId)}`);
}

export function saveDmaicPilotPlan(projectId: string, payload: {
  expected_storage_version: number;
  pilot_type: "before_after" | "controlled_trial" | "doe_confirmation";
  scope: string;
  study_design: string;
  sample_plan: string;
  duration: string;
  success_metrics: string[];
  stop_criteria: string[];
  risk_responses: string[];
  analysis_run_ids: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/pilot-plans`, { method: "POST", body: JSON.stringify(payload) });
}

export function getDmaicPilotPlan(projectId: string, documentId: string): Promise<StoredDmaicPilotPlan> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/pilot-plans/${encodeURIComponent(documentId)}`);
}

export function saveDmaicControlHandoff(projectId: string, payload: {
  expected_storage_version: number;
  monitoring_plan: string;
  review_frequency: string;
  effectiveness_criteria: string[];
  reaction_plans: Array<{
    trigger: string;
    action: string;
    owner_ref: string;
    escalation_ref: string | null;
    response_time: string;
  }>;
  fmea_study_id: string;
  fmea_control_ids: string[];
  analysis_run_ids: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredDmaicProject> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/control-handoffs`, {
    method: "POST", body: JSON.stringify(payload),
  });
}

export function getDmaicControlHandoff(projectId: string, documentId: string): Promise<StoredDmaicControlHandoff> {
  return request(`/v1/dmaic-projects/${encodeURIComponent(projectId)}/control-handoffs/${encodeURIComponent(documentId)}`);
}

export type DoeReportTemplate = "standard" | "customer_review" | "regulatory_review";

export function doeRunArtifactUrl(runId: string, artifact: "html" | "zip", template: DoeReportTemplate = "standard"): string {
  const suffix = artifact === "html" ? "report.html" : "export";
  const templateQuery = template === "standard" ? "" : `?template_id=${encodeURIComponent(template)}`;
  return `${API_BASE}/v1/analysis-runs/${encodeURIComponent(runId)}/${suffix}${templateQuery}`;
}

export function createImrRun(payload: {
  run_id: string;
  values: number[];
  target?: number;
  rules: "basic" | "western_electric" | "nelson";
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/imr", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createXbarSRun(payload: {
  run_id: string;
  subgroups: number[][];
  rules: "basic" | "nelson";
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/xbar-s", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createXbarRRun(payload: {
  run_id: string;
  subgroups: number[][];
  rules: "basic" | "nelson";
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/xbar-r", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createEwmaRun(payload: {
  run_id: string;
  values: number[];
  target?: number;
  sigma?: number;
  weight: number;
  limit_width: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/ewma", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createCusumRun(payload: {
  run_id: string;
  values: number[];
  target?: number;
  sigma?: number;
  reference_value: number;
  decision_interval: number;
  fir_head_start?: number;
  reset_after_signal?: boolean;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/cusum", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createAttributeChartRun(payload: {
  run_id: string;
  chart: "p" | "np" | "c" | "u" | "p_prime" | "u_prime";
  counts: number[];
  opportunities: number[];
}): Promise<StoredRun> {
  const { chart, run_id, counts, opportunities } = payload;
  const body = chart === "p" || chart === "np" || chart === "p_prime"
    ? { run_id, nonconforming: counts, sample_sizes: opportunities }
    : { run_id, defects: counts, inspection_units: opportunities };
  const path = chart === "p_prime" ? "laney-p-prime" : chart === "u_prime" ? "laney-u-prime" : `${chart}-chart`;
  return request(`/v1/analysis-runs/${path}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createRareEventChartRun(payload: {
  run_id: string;
  chart: "g" | "t";
  intervals: number[];
  alpha: number;
  baseline_mean_interval?: number;
}): Promise<StoredRun> {
  const { chart, run_id, intervals, alpha, baseline_mean_interval } = payload;
  const body = chart === "g"
    ? { run_id, opportunities_between_events: intervals, alpha, ...(baseline_mean_interval === undefined ? {} : { baseline_mean_interval }) }
    : { run_id, time_between_events: intervals, alpha, ...(baseline_mean_interval === undefined ? {} : { baseline_mean_interval }) };
  return request(`/v1/analysis-runs/${chart}-chart`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createCapabilityRun(payload: {
  run_id: string;
  values: number[];
  lsl?: number;
  usl?: number;
  target?: number;
  model: "normal" | "nonnormal";
}): Promise<StoredRun> {
  const { model, ...body } = payload;
  return request(`/v1/analysis-runs/capability-${model}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createGageRrRun(payload: {
  run_id: string;
  records: Array<{ part: string; operator: string; measurement: number }>;
  study_variation_multiplier: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/gage-rr-crossed", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createAttributeAgreementRun(payload: {
  run_id: string;
  records: Array<{ item: string; appraiser: string; trial: number; rating: string; standard: string }>;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/attribute-agreement", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createGageBiasLinearityRun(payload: {
  run_id: string;
  records: Array<{ reference: number; measurement: number }>;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/gage-bias-linearity", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeAnalysisRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  responses: number[];
  response_name: string;
  replicates: number;
  center_points: number;
  blocks: 1 | 2 | 4 | 8 | 16;
  randomize: boolean;
  seed: number;
  interaction_order: number;
  prediction_points: Array<Record<string, number>>;
  optimization_goal: "maximize" | "minimize";
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-full-factorial-analysis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeFractionalFactorialRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  generators: Array<{ factor: string; terms: string[] }>;
  block_generators: string[][];
  replicates: number;
  foldover: boolean;
  foldover_factor: string | null;
  randomize: boolean;
  seed: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-fractional-factorial", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeFractionalFactorialAnalysisRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  generators: Array<{ factor: string; terms: string[] }>;
  block_generators: string[][];
  responses: number[];
  response_name: string;
  replicates: number;
  foldover: boolean;
  foldover_factor: string | null;
  randomize: boolean;
  seed: number;
  alpha: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-fractional-factorial-analysis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type DoeAutomaticFractionalPayload = {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  runs?: number;
  minimum_resolution: number;
  block_generators: string[][];
  replicates: number;
  foldover: boolean;
  foldover_factor: string | null;
  randomize: boolean;
  seed: number;
};

export function createDoeAutomaticFractionalFactorialRun(payload: DoeAutomaticFractionalPayload): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-fractional-factorial-auto", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeAutomaticFractionalFactorialAnalysisRun(payload: DoeAutomaticFractionalPayload & {
  responses: number[];
  response_name: string;
  alpha: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-fractional-factorial-auto-analysis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoePlackettBurmanRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  runs?: number;
  replicates: number;
  center_points: number;
  randomize: boolean;
  seed: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-plackett-burman", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type DoeCentralCompositePayload = {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  design_type: "rotatable" | "face_centered";
  center_points: number;
  replicates: number;
  randomize: boolean;
  seed: number;
};

export function createDoeBoxBehnkenRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  center_points?: number;
  replicates: number;
  randomize: boolean;
  seed: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-box-behnken", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeBoxBehnkenAnalysisRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  center_points?: number;
  replicates: number;
  randomize: boolean;
  seed: number;
  responses: number[];
  response_name: string;
  alpha: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-box-behnken-analysis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeBoxBehnkenSurfaceRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  center_points?: number;
  replicates: number;
  randomize: boolean;
  seed: number;
  responses: number[];
  response_name: string;
  alpha: number;
  plot_factors: [string, string];
  hold_values: Record<string, number>;
  grid_size: number;
  contour_levels: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-box-behnken-surface", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeCentralCompositeRun(payload: DoeCentralCompositePayload): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-central-composite", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeCentralCompositeAnalysisRun(payload: DoeCentralCompositePayload & {
  responses: number[];
  response_name: string;
  alpha: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-central-composite-analysis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoeCentralCompositeSurfaceRun(payload: DoeCentralCompositePayload & {
  responses: number[];
  response_name: string;
  alpha: number;
  plot_factors: [string, string];
  hold_values: Record<string, number>;
  grid_size: number;
  contour_levels: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-central-composite-surface", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createDoePlackettBurmanAnalysisRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  responses: number[];
  response_name: string;
  runs?: number;
  replicates: number;
  center_points: number;
  randomize: boolean;
  seed: number;
  alpha: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-plackett-burman-analysis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type DoeResponseObjectivePayload = {
  name: string;
  responses: number[];
  goal: "maximize" | "minimize" | "target";
  lower?: number;
  target: number;
  upper?: number;
  weight: number;
  importance: number;
};

export function createDoeResponseOptimizerRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  objectives: DoeResponseObjectivePayload[];
  replicates: number;
  center_points: number;
  randomize: boolean;
  seed: number;
  interaction_order: number;
  factor_constraints: Record<string, { lower: number; upper: number }>;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-response-optimizer", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listFmeaStudies(limit = 50): Promise<FmeaStudyPage> {
  return request(`/v1/fmea-studies?limit=${limit}`);
}

export function getFmeaStudy(studyId: string): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}`);
}

export function getFmeaStudyReport(studyId: string): Promise<FmeaStudyReport> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/report`);
}

export function createFmeaStudy(payload: {
  study_id: string;
  name: string;
  study_type: "design" | "process";
  standard_version: string;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request("/v1/fmea-studies", { method: "POST", body: JSON.stringify(payload) });
}

export function listActionPriorityPolicies(limit = 100): Promise<ActionPriorityPolicyPage> {
  return request(`/v1/fmea-action-priority-policies?limit=${limit}`);
}

export function createActionPriorityPolicy(payload: {
  policy_id: string;
  standard_version: string;
  entries: Array<{ severity: number; occurrence: number; detection: number; priority: string }>;
}): Promise<StoredActionPriorityPolicy> {
  return request("/v1/fmea-action-priority-policies", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function attachActionPriorityPolicy(studyId: string, payload: {
  expected_storage_version: number;
  policy_key: string;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/action-priority-policy`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addFmeaFailure(studyId: string, payload: {
  expected_storage_version: number;
  item_id: string;
  structure_element: string;
  function: string;
  requirement: string;
  failure_mode: string;
  effect: string;
  cause: string;
  prevention_control: string;
  detection_control: string;
  ratings: { severity: number; occurrence: number; detection: number };
  process_step_id?: string | null;
  characteristic_ids?: string[];
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/failure-analyses`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addFmeaProcessStep(studyId: string, payload: {
  expected_storage_version: number;
  step_id: string;
  sequence: number;
  name: string;
  operation: string;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/process-steps`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addFmeaProcessCharacteristic(studyId: string, payload: {
  expected_storage_version: number;
  characteristic_id: string;
  process_step_id: string;
  name: string;
  characteristic_type: "product" | "process";
  specification: string;
  special_classification?: string | null;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/process-characteristics`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addFmeaControlPlanItem(studyId: string, payload: {
  expected_storage_version: number;
  control_id: string;
  phase: "prototype" | "pre_launch" | "production" | "safe_launch";
  characteristic_id: string;
  failure_item_ids: string[];
  measurement_method: string;
  sample_size: number;
  frequency: string;
  control_method: string;
  reaction_plan: string;
  reaction_owner: string;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/control-plan-items`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function linkFmeaControlPlanAnalysisEvidence(studyId: string, controlId: string, payload: {
  expected_storage_version: number;
  run_id: string;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/control-plan-items/${encodeURIComponent(controlId)}/analysis-evidence`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitFmeaForReview(studyId: string, payload: {
  expected_storage_version: number;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/submit-review`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function addFmeaAction(studyId: string, payload: {
  expected_storage_version: number;
  action_id: string;
  item_id: string;
  description: string;
  owner: string;
  due_date: string;
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/recommended-actions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function completeFmeaAction(studyId: string, actionId: string, payload: {
  expected_storage_version: number;
  result: string;
  evidence_refs: string[];
  revised_ratings: { severity: number; occurrence: number; detection: number };
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/recommended-actions/${encodeURIComponent(actionId)}/complete`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function approveFmeaStudy(studyId: string, payload: {
  expected_storage_version: number;
  user_id: string;
  password: string;
  meaning: "approval";
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/approve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listWorksheets(limit = 50): Promise<WorksheetPage> {
  return request(`/v1/worksheets?limit=${limit}`);
}

export function getWorksheet(worksheetId: string): Promise<StoredWorksheet> {
  return request(`/v1/worksheets/${encodeURIComponent(worksheetId)}`);
}

export function importCsvWorksheet(payload: {
  file_name: string;
  worksheet_name: string;
  content_base64: string;
}): Promise<StoredWorksheet> {
  return request("/v1/worksheets/import-csv", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function replaceWorksheetCell(worksheetId: string, payload: {
  expected_storage_version: number;
  row_index: number;
  column_name: string;
  value: CellValue;
}): Promise<StoredWorksheet> {
  return request(`/v1/worksheets/${encodeURIComponent(worksheetId)}/cells`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function createCheckSheet(payload: {
  sheet_id: string;
  title: string;
  process_name: string;
  category_label: string;
}): Promise<StoredCheckSheet> {
  return request("/v1/spc/check-sheets", { method: "POST", body: JSON.stringify(payload) });
}

export function getCheckSheet(sheetId: string): Promise<StoredCheckSheet> {
  return request(`/v1/spc/check-sheets/${encodeURIComponent(sheetId)}`);
}

export function addCheckSheetRecord(sheetId: string, payload: {
  expected_storage_version: number;
  record_id: string;
  category: string;
  count: number;
  observed_at?: string | null;
  location?: string | null;
  shift?: string | null;
  lot?: string | null;
  note?: string | null;
}): Promise<StoredCheckSheet> {
  return request(`/v1/spc/check-sheets/${encodeURIComponent(sheetId)}/records`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createFishbone(payload: {
  diagram_id: string;
  title: string;
  process_name: string;
  problem_statement: string;
  categories: Array<{ category_id: string; name: string }>;
}): Promise<StoredFishbone> {
  return request("/v1/spc/fishbone-diagrams", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getFishbone(diagramId: string): Promise<StoredFishbone> {
  return request(`/v1/spc/fishbone-diagrams/${encodeURIComponent(diagramId)}`);
}

export function addFishboneCause(diagramId: string, payload: {
  expected_storage_version: number;
  category_id: string;
  cause_id: string;
  text: string;
  evidence_refs: string[];
  selected_for_verification: boolean;
}): Promise<StoredFishbone> {
  return request(`/v1/spc/fishbone-diagrams/${encodeURIComponent(diagramId)}/causes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createParetoRun(payload: {
  run_id: string;
  subject: string;
  metric_kind: "frequency" | "cost" | "loss";
  threshold_percentage: number;
  items: Array<{ category: string; value: number }>;
  source_sheet_id?: string | null;
  source_snapshot_digest?: string | null;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/pareto", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

import type { ApiError, CellValue, FmeaStudyPage, StoredFmeaStudy, RunPage, StoredRun, StoredWorksheet, WorksheetPage } from "./types";

const API_BASE = import.meta.env.VITE_STATPRO_API_URL ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const payload = (await response.json()) as T | ApiError;
  if (!response.ok) {
    const error = payload as ApiError;
    throw new Error(error.error?.message ?? "요청을 완료하지 못했습니다.");
  }
  return payload as T;
}

export function listRuns(limit = 20): Promise<RunPage> {
  return request(`/v1/analysis-runs?limit=${limit}`);
}

export function getHealth(): Promise<{ status: string; engine_version: string }> {
  return request("/health");
}

export function getRun(runId: string): Promise<StoredRun> {
  return request(`/v1/analysis-runs/${encodeURIComponent(runId)}`);
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

export function createDoeAnalysisRun(payload: {
  run_id: string;
  factors: Array<{ name: string; low: number; high: number }>;
  responses: number[];
  response_name: string;
  replicates: number;
  center_points: number;
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
  replicates: number;
  foldover: boolean;
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
  responses: number[];
  response_name: string;
  replicates: number;
  foldover: boolean;
  randomize: boolean;
  seed: number;
  alpha: number;
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/doe-fractional-factorial-analysis", {
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
  actor: string;
  occurred_at: string;
}): Promise<StoredFmeaStudy> {
  return request(`/v1/fmea-studies/${encodeURIComponent(studyId)}/failure-analyses`, {
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
  actor: string;
  occurred_at: string;
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

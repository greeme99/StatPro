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
}): Promise<StoredRun> {
  return request("/v1/analysis-runs/imr", {
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

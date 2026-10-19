export type ResultBundle = {
  analysis_type: string;
  engine_version: string;
  input_digest: string;
  parameters: Record<string, unknown>;
  tables: Record<string, any>;
  plots: Record<string, any>;
  diagnostics: Record<string, unknown>;
  assumptions: string[];
  warnings: string[];
  provenance: Array<{ title: string; url: string; authority: string }>;
};

export type StoredRun = {
  run_id: string;
  storage_version: number;
  etag: string;
  result: ResultBundle;
};

export type RunPage = {
  items: StoredRun[];
  next_after: string | null;
};

export type ApiError = {
  ok: false;
  error: { code: string; message: string; field?: string | null };
};

export type RiskRatings = {
  severity: number;
  occurrence: number;
  detection: number;
  rpn: number;
};

export type FailureAnalysis = {
  item_id: string;
  structure_element: string;
  function: string;
  requirement: string;
  failure_mode: string;
  effect: string;
  cause: string;
  prevention_control: string;
  detection_control: string;
  initial_ratings: RiskRatings;
  current_ratings: RiskRatings;
  action_priority: string | null;
  action_priority_reason: string | null;
};

export type RecommendedAction = {
  action_id: string;
  item_id: string;
  description: string;
  owner: string;
  due_date: string;
  status: "open" | "in_progress" | "complete" | "cancelled";
  result: string | null;
  evidence_refs: string[];
};

export type FmeaStudy = {
  study_id: string;
  name: string;
  study_type: "design" | "process";
  standard_version: string;
  status: "draft" | "in_review" | "approved" | "archived";
  revision: number;
  parent_digest: string | null;
  digest: string;
  items: FailureAnalysis[];
  actions: RecommendedAction[];
  audit_events: Array<{
    sequence: number;
    event_type: string;
    actor: string;
    occurred_at: string;
    details: Record<string, unknown>;
  }>;
  action_priority_policy_id: string | null;
  action_priority_policy_digest: string | null;
};

export type StoredFmeaStudy = {
  study_id: string;
  storage_version: number;
  etag: string;
  study: FmeaStudy;
};

export type FmeaStudyPage = {
  items: StoredFmeaStudy[];
  next_after: string | null;
};

export type CellValue = number | boolean | string | null;

export type DataColumn = {
  name: string;
  data_type: "numeric" | "categorical" | "text" | "datetime" | "logical";
  nullable: boolean;
  missing_count: number;
  values: CellValue[];
};

export type DatasetSnapshot = {
  dataset_id: string;
  digest: string;
  source: {
    kind: string;
    location: string;
    media_type: string;
    content_digest: string;
  };
  row_count: number;
  column_count: number;
  columns: DataColumn[];
};

export type WorksheetSnapshot = {
  worksheet_id: string;
  name: string;
  base_dataset_digest: string;
  digest: string;
  revision: number;
  parent_digest: string | null;
  row_count: number;
  columns: DataColumn[];
  transformations: Array<Record<string, unknown>>;
};

export type StoredWorksheet = {
  worksheet_id: string;
  storage_version: number;
  etag: string;
  worksheet: WorksheetSnapshot;
  dataset: DatasetSnapshot | null;
};

export type WorksheetPage = {
  items: StoredWorksheet[];
  next_after: string | null;
};

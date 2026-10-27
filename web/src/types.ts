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
  process_step_id: string | null;
  characteristic_ids: string[];
};

export type ProcessStep = {
  step_id: string;
  sequence: number;
  name: string;
  operation: string;
};

export type ProcessCharacteristic = {
  characteristic_id: string;
  process_step_id: string;
  name: string;
  characteristic_type: "product" | "process";
  specification: string;
  special_classification: string | null;
};

export type ControlPlanItem = {
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
  analysis_evidence?: Array<{
    run_id: string;
    analysis_type: string;
    run_etag: string;
    input_digest: string;
  }>;
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

export type SevenStepProgress = {
  step_number: number;
  step_id: "planning_and_preparation" | "structure_analysis" | "function_analysis" | "failure_analysis" | "risk_analysis" | "optimization" | "results_documentation";
  title: string;
  status: "not_started" | "in_progress" | "complete";
  evidence_count: number;
  gaps: string[];
};

export type ActionPriorityEntry = {
  severity: number;
  occurrence: number;
  detection: number;
  priority: string;
};

export type ActionPriorityPolicy = {
  policy_key: string;
  policy_id: string;
  standard_version: string;
  digest: string;
  entries: ActionPriorityEntry[];
};

export type StoredActionPriorityPolicy = {
  policy_key: string;
  storage_version: number;
  etag: string;
  policy: ActionPriorityPolicy;
};

export type ActionPriorityPolicyPage = {
  items: StoredActionPriorityPolicy[];
  next_after: string | null;
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
  action_priority_policy_key: string | null;
  process_steps: ProcessStep[];
  characteristics: ProcessCharacteristic[];
  control_plan_items: ControlPlanItem[];
  seven_step_progress?: SevenStepProgress[];
};

export type StoredFmeaStudy = {
  study_id: string;
  storage_version: number;
  etag: string;
  study: FmeaStudy;
};

export type FmeaStudyReport = {
  report_type: string;
  study_id: string;
  study_name: string;
  study_type: "design" | "process";
  standard_version: string;
  revision: number;
  snapshot_digest: string;
  status: FmeaStudy["status"];
  action_priority_policy: { policy_id: string | null; policy_digest: string | null };
  seven_step_progress: SevenStepProgress[];
  rows: Array<{
    failure: FailureAnalysis;
    process_step: ProcessStep | null;
    characteristics: ProcessCharacteristic[];
    control_plan_items: ControlPlanItem[];
    actions: RecommendedAction[];
  }>;
  approval_record: { actor: string; occurred_at: string; audit_sequence: number } | null;
  audit_events: FmeaStudy["audit_events"];
  analysis_evidence_checks: Array<{ control_id: string; run_id: string; status: "verified" | "missing" | "mismatch" | "unavailable" }> | null;
  limitations: string[];
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

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
  actions: Array<Record<string, unknown>>;
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

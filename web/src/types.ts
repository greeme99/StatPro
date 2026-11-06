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

export type CheckSheetRecord = {
  record_id: string;
  category: string;
  count: number;
  observed_at: string | null;
  location: string | null;
  shift: string | null;
  lot: string | null;
  note: string | null;
};

export type CheckSheetSnapshot = {
  sheet_id: string;
  title: string;
  process_name: string;
  category_label: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  records: CheckSheetRecord[];
};

export type StoredCheckSheet = {
  sheet_id: string;
  storage_version: number;
  etag: string;
  sheet: CheckSheetSnapshot;
  summary: ResultBundle;
};

export type FishboneCause = {
  cause_id: string;
  text: string;
  evidence_refs: string[];
  selected_for_verification: boolean;
};

export type FishboneCategory = {
  category_id: string;
  name: string;
  causes: FishboneCause[];
};

export type FishboneSnapshot = {
  diagram_id: string;
  title: string;
  process_name: string;
  problem_statement: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  categories: FishboneCategory[];
};

export type StoredFishbone = {
  diagram_id: string;
  storage_version: number;
  etag: string;
  diagram: FishboneSnapshot;
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

export type QualityMetricSnapshot = {
  metric_id: string;
  name: string;
  unit: string;
  value: number;
  status: "good" | "warning" | "critical";
  source: {
    run_id: string;
    run_etag: string;
    analysis_type: string;
    engine_version: string;
    input_digest: string;
    value_path: string;
  };
  refresh_cycle: string;
  owner_ref: string;
  captured_at: string;
  lower_warning: number | null;
  lower_critical: number | null;
  upper_warning: number | null;
  upper_critical: number | null;
  digest: string;
};

export type StoredQualityMetric = {
  metric_id: string;
  storage_version: number;
  etag: string;
  metric: QualityMetricSnapshot;
};

export type QualityMetricPage = {
  items: StoredQualityMetric[];
  next_after: string | null;
};

export type DefectCategory = {
  category: string;
  defect_count: number;
  opportunity_count: number;
  unit_loss: number;
  severity: number;
};

export type DefectAnalysisSnapshot = {
  analysis_id: string;
  title: string;
  process_name: string;
  period: string;
  owner_ref: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  source: null | { check_sheet_id: string; check_sheet_etag: string; check_sheet_digest: string };
  categories: DefectCategory[];
};

export type DefectAnalysisSummary = {
  total_defects: number;
  total_opportunities: number;
  dpmo: number;
  estimated_loss: number;
  top_risk_category: string;
  categories: Array<DefectCategory & { dpmo: number; estimated_loss: number; risk_score: number }>;
};

export type StoredDefectAnalysis = {
  analysis_id: string;
  storage_version: number;
  etag: string;
  analysis: DefectAnalysisSnapshot;
  summary: DefectAnalysisSummary;
};

export type DefectAnalysisPage = {
  items: StoredDefectAnalysis[];
  next_after: string | null;
};

export type DmaicDocumentReference = {
  document_type: string;
  document_id: string;
  revision: number;
  digest: string;
};

export type DmaicProject = {
  project_id: string;
  title: string;
  owner_ref: string;
  sponsor_ref: string | null;
  champion_ref: string | null;
  department: string | null;
  start_date: string | null;
  target_end_date: string | null;
  status: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  charter: DmaicDocumentReference | null;
  voice_of_customer: DmaicDocumentReference | null;
  sipoc: DmaicDocumentReference | null;
  stakeholder_assessment: DmaicDocumentReference | null;
  problem_definition: DmaicDocumentReference | null;
  measurement_plan: DmaicDocumentReference | null;
  root_cause_analysis: DmaicDocumentReference | null;
  solution_selection: DmaicDocumentReference | null;
  pilot_plan: DmaicDocumentReference | null;
  control_handoff: DmaicDocumentReference | null;
};

export type StoredDmaicProject = {
  project_id: string;
  storage_version: number;
  etag: string;
  project: DmaicProject;
};

export type DmaicProjectPage = {
  items: StoredDmaicProject[];
  next_after: string | null;
};

export type DmaicMeasurementPlan = {
  document_id: string;
  project_id: string;
  revision: number;
  digest: string;
  primary_metric: string;
  source_documents: DmaicDocumentReference[];
  analysis_evidence: Array<{ run_id: string; analysis_type: string; run_etag: string; input_digest: string }>;
};

export type StoredDmaicMeasurementPlan = {
  document_id: string;
  storage_version: number;
  etag: string;
  measurement_plan: DmaicMeasurementPlan;
};

export type DmaicRootCauseAnalysis = {
  document_id: string;
  project_id: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  problem_statement: string;
  method: "fishbone_pareto" | "five_whys" | "data_analysis";
  candidate_causes: string[];
  verified_causes: string[];
  next_actions: string[];
  source_documents: DmaicDocumentReference[];
  analysis_evidence: Array<{ run_id: string; analysis_type: string; run_etag: string; input_digest: string }>;
  actor: string;
  occurred_at: string;
};

export type StoredDmaicRootCauseAnalysis = {
  document_id: string;
  storage_version: number;
  etag: string;
  root_cause_analysis: DmaicRootCauseAnalysis;
};

export type DmaicSolutionSelection = {
  document_id: string;
  project_id: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  problem_statement: string;
  candidate_solutions: string[];
  selected_solution: string;
  decision_rationale: string;
  validation_plan: string;
  source_documents: DmaicDocumentReference[];
  analysis_evidence: Array<{ run_id: string; analysis_type: string; run_etag: string; input_digest: string }>;
  actor: string;
  occurred_at: string;
};

export type StoredDmaicSolutionSelection = {
  document_id: string;
  storage_version: number;
  etag: string;
  solution_selection: DmaicSolutionSelection;
};

export type DmaicPilotPlan = {
  document_id: string;
  project_id: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  pilot_type: "before_after" | "controlled_trial" | "doe_confirmation";
  scope: string;
  study_design: string;
  sample_plan: string;
  duration: string;
  success_metrics: string[];
  stop_criteria: string[];
  risk_responses: string[];
  source_documents: DmaicDocumentReference[];
  analysis_evidence: Array<{ run_id: string; analysis_type: string; run_etag: string; input_digest: string }>;
  actor: string;
  occurred_at: string;
};

export type StoredDmaicPilotPlan = {
  document_id: string;
  storage_version: number;
  etag: string;
  pilot_plan: DmaicPilotPlan;
};

export type DmaicAnalysisEvidenceReference = {
  run_id: string;
  analysis_type: string;
  run_etag: string;
  input_digest: string;
};

export type DmaicFmeaControlPlanReference = {
  study_id: string;
  study_etag: string;
  study_digest: string;
  control_ids: string[];
};

export type DmaicReactionPlanItem = {
  trigger: string;
  action: string;
  owner_ref: string;
  escalation_ref: string | null;
  response_time: string;
};

export type DmaicControlHandoff = {
  document_id: string;
  project_id: string;
  revision: number;
  parent_digest: string | null;
  digest: string;
  monitoring_plan: string;
  review_frequency: string;
  effectiveness_criteria: string[];
  reaction_plans: DmaicReactionPlanItem[];
  source_documents: DmaicDocumentReference[];
  fmea_control_plan: DmaicFmeaControlPlanReference;
  analysis_evidence: DmaicAnalysisEvidenceReference[];
  actor: string;
  occurred_at: string;
};

export type StoredDmaicControlHandoff = {
  document_id: string;
  storage_version: number;
  etag: string;
  control_handoff: DmaicControlHandoff;
};

export type DmaicCharter = {
  document_id: string;
  project_id: string;
  revision: number;
  digest: string;
  problem_statement: string;
  success_metrics: string[];
};

export type StoredDmaicCharter = {
  document_id: string;
  storage_version: number;
  etag: string;
  charter: DmaicCharter;
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
  approval_record: {
    actor: string;
    occurred_at: string;
    audit_sequence: number;
    authenticated: boolean;
    authorization_context: {
      policy: { require_independent_approver: boolean };
      prior_actor_match_count: number | null;
      prior_actor_identity_match: boolean | null;
      actor_identity_limit: string;
    } | null;
    electronic_signature: {
      signer_id: string;
      signer_name: string;
      role: string;
      meaning: "approval";
      authority: string;
      authentication_method: string;
      signed_digest: string;
      executed_at: string;
    } | null;
  } | null;
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

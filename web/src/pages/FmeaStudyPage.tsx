import { AlertTriangle, ArrowLeft, CheckCircle2, ClipboardCheck, FilePlus2, GitBranch, Link2, ShieldAlert, Upload, Wrench } from "lucide-react";
import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { addFmeaAction, addFmeaControlPlanItem, addFmeaFailure, addFmeaProcessCharacteristic, addFmeaProcessStep, approveFmeaStudy, attachActionPriorityPolicy, completeFmeaAction, createActionPriorityPolicy, getFmeaStudy, getFmeaStudyReport, listActionPriorityPolicies, submitFmeaForReview } from "../api";
import { Button } from "../components/Button";
import type { FailureAnalysis, FmeaStudyReport, RecommendedAction, StoredActionPriorityPolicy, StoredFmeaStudy } from "../types";

const statusLabels = { draft: "작성 중", in_review: "검토 중", approved: "승인됨", archived: "보관됨" };
const stepStatusLabels = { not_started: "미착수", in_progress: "진행 중", complete: "완료" };
const stepTitles: Record<string, string> = {
  planning_and_preparation: "기획 및 준비",
  structure_analysis: "구조 분석",
  function_analysis: "기능 분석",
  failure_analysis: "고장 분석",
  risk_analysis: "위험 분석",
  optimization: "최적화",
  results_documentation: "결과 문서화",
};

export function FmeaStudyPage() {
  const { studyId = "" } = useParams();
  const itemIdRef = useRef<HTMLInputElement>(null);
  const [stored, setStored] = useState<StoredFmeaStudy | null>(null);
  const [policies, setPolicies] = useState<StoredActionPriorityPolicy[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showActionForm, setShowActionForm] = useState(false);
  const [traceEditor, setTraceEditor] = useState<"step" | "characteristic" | "control" | null>(null);
  const [completingActionId, setCompletingActionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<FmeaStudyReport | null>(null);
  const [reportBusy, setReportBusy] = useState(false);
  const [reportError, setReportError] = useState("");
  const selected = useMemo(() => stored?.study.items.find((item) => item.item_id === selectedId) ?? null, [stored, selectedId]);

  async function handleLoadReport() {
    setReportBusy(true);
    setReportError("");
    try {
      setReport(await getFmeaStudyReport(studyId));
    } catch (requestError) {
      setReportError(requestError instanceof Error ? requestError.message : "보고서를 불러오지 못했습니다.");
    } finally { setReportBusy(false); }
  }

  useEffect(() => {
    let active = true;
    getFmeaStudy(studyId)
      .then((value) => { if (active) { setStored(value); setSelectedId(value.study.items[0]?.item_id ?? null); } })
      .catch((requestError) => { if (active) setError(requestError instanceof Error ? requestError.message : "Study를 불러오지 못했습니다."); });
    listActionPriorityPolicies()
      .then((page) => { if (active) setPolicies(Array.isArray(page.items) ? page.items : []); })
      .catch(() => { if (active) setPolicies([]); });
    return () => { active = false; };
  }, [studyId]);

  async function handleAddFailure(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const itemId = String(form.get("item_id") ?? "").trim();
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(itemId)) {
      setError("항목 ID 형식을 확인하세요.");
      itemIdRef.current?.focus();
      return;
    }
    setBusy(true);
    setError("");
    try {
      const revised = await addFmeaFailure(studyId, {
        expected_storage_version: stored.storage_version,
        item_id: itemId,
        structure_element: String(form.get("structure_element") ?? "").trim(),
        function: String(form.get("function") ?? "").trim(),
        requirement: String(form.get("requirement") ?? "").trim(),
        failure_mode: String(form.get("failure_mode") ?? "").trim(),
        effect: String(form.get("effect") ?? "").trim(),
        cause: String(form.get("cause") ?? "").trim(),
        prevention_control: String(form.get("prevention_control") ?? "").trim(),
        detection_control: String(form.get("detection_control") ?? "").trim(),
        ratings: {
          severity: Number(form.get("severity")), occurrence: Number(form.get("occurrence")), detection: Number(form.get("detection")),
        },
        process_step_id: String(form.get("process_step_id") ?? "").trim() || null,
        characteristic_ids: form.getAll("characteristic_ids").map(String).filter(Boolean),
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      });
      setStored(revised);
      setSelectedId(itemId);
      setShowForm(false);
      formElement.reset();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "고장 분석을 추가하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleAddProcessStep(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    try {
      setStored(await addFmeaProcessStep(studyId, {
        expected_storage_version: stored.storage_version,
        step_id: String(form.get("step_id") ?? "").trim(),
        sequence: Number(form.get("sequence")),
        name: String(form.get("name") ?? "").trim(),
        operation: String(form.get("operation") ?? "").trim(),
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      }));
      formElement.reset();
      setTraceEditor(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "공정 단계를 추가하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleAddCharacteristic(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    try {
      setStored(await addFmeaProcessCharacteristic(studyId, {
        expected_storage_version: stored.storage_version,
        characteristic_id: String(form.get("characteristic_id") ?? "").trim(),
        process_step_id: String(form.get("process_step_id") ?? ""),
        name: String(form.get("name") ?? "").trim(),
        characteristic_type: String(form.get("characteristic_type")) as "product" | "process",
        specification: String(form.get("specification") ?? "").trim(),
        special_classification: String(form.get("special_classification") ?? "").trim() || null,
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      }));
      formElement.reset();
      setTraceEditor(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "공정 특성을 추가하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleAddControlPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    try {
      setStored(await addFmeaControlPlanItem(studyId, {
        expected_storage_version: stored.storage_version,
        control_id: String(form.get("control_id") ?? "").trim(),
        phase: String(form.get("phase")) as "prototype" | "pre_launch" | "production" | "safe_launch",
        characteristic_id: String(form.get("characteristic_id") ?? ""),
        failure_item_ids: form.getAll("failure_item_ids").map(String).filter(Boolean),
        measurement_method: String(form.get("measurement_method") ?? "").trim(),
        sample_size: Number(form.get("sample_size")),
        frequency: String(form.get("frequency") ?? "").trim(),
        control_method: String(form.get("control_method") ?? "").trim(),
        reaction_plan: String(form.get("reaction_plan") ?? "").trim(),
        reaction_owner: String(form.get("reaction_owner") ?? "").trim(),
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      }));
      formElement.reset();
      setTraceEditor(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Control Plan 항목을 추가하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleSubmitReview() {
    if (!stored) return;
    setBusy(true);
    setError("");
    try {
      setStored(await submitFmeaForReview(studyId, { expected_storage_version: stored.storage_version, actor: "quality.reviewer", occurred_at: new Date().toISOString() }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "검토 요청을 완료하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleAddAction(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    try {
      const revised = await addFmeaAction(studyId, {
        expected_storage_version: stored.storage_version,
        action_id: String(form.get("action_id") ?? "").trim(),
        item_id: String(form.get("item_id") ?? "").trim(),
        description: String(form.get("description") ?? "").trim(),
        owner: String(form.get("owner") ?? "").trim(),
        due_date: String(form.get("due_date") ?? ""),
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      });
      setStored(revised);
      setShowActionForm(false);
      formElement.reset();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "권고조치를 추가하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleCompleteAction(event: FormEvent<HTMLFormElement>, action: RecommendedAction) {
    event.preventDefault();
    if (!stored) return;
    const item = stored.study.items.find((candidate) => candidate.item_id === action.item_id);
    if (!item) { setError("권고조치에 연결된 고장 분석을 찾지 못했습니다."); return; }
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const revised = await completeFmeaAction(studyId, action.action_id, {
        expected_storage_version: stored.storage_version,
        result: String(form.get("result") ?? "").trim(),
        evidence_refs: String(form.get("evidence_refs") ?? "").split(/\r?\n/).map((value) => value.trim()).filter(Boolean),
        revised_ratings: {
          severity: Number(form.get("severity")),
          occurrence: Number(form.get("occurrence")),
          detection: Number(form.get("detection")),
        },
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      });
      setStored(revised);
      setCompletingActionId(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "권고조치를 완료하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleApprove() {
    if (!stored) return;
    setBusy(true);
    setError("");
    try {
      setStored(await approveFmeaStudy(studyId, { expected_storage_version: stored.storage_version, actor: "quality.approver", occurred_at: new Date().toISOString() }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Study를 승인하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleAttachPolicy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      setStored(await attachActionPriorityPolicy(studyId, {
        expected_storage_version: stored.storage_version,
        policy_key: String(form.get("policy_key") ?? ""),
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      }));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "AP 정책을 연결하지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function handleImportPolicy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const lines = String(form.get("entries") ?? "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    const entries = lines.map((line) => {
      const [severity, occurrence, detection, priority, ...extra] = line.split(/[\t,;]/).map((value) => value.trim());
      return { severity: Number(severity), occurrence: Number(occurrence), detection: Number(detection), priority, valid: extra.length === 0 && Boolean(priority) };
    });
    if (entries.length === 0 || entries.some((entry) => !entry.valid || ![entry.severity, entry.occurrence, entry.detection].every((value) => Number.isInteger(value) && value >= 1 && value <= 10))) {
      setError("AP 항목은 한 줄에 S,O,D,우선순위 형식으로 입력하고 S/O/D는 1–10 정수여야 합니다.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const created = await createActionPriorityPolicy({
        policy_id: String(form.get("policy_id") ?? "").trim(),
        standard_version: String(form.get("standard_version") ?? "").trim(),
        entries: entries.map(({ severity, occurrence, detection, priority }) => ({ severity, occurrence, detection, priority })),
      });
      setPolicies((current) => [...current.filter((item) => item.policy_key !== created.policy_key), created].sort((left, right) => left.policy_key.localeCompare(right.policy_key)));
      formElement.reset();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "AP 정책을 가져오지 못했습니다.");
    } finally { setBusy(false); }
  }

  if (!stored) return <div className="page" data-density="compact">{error ? <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div> : <div className="skeleton page-skeleton" aria-label="FMEA Study 불러오는 중" />}</div>;
  const { study } = stored;
  const processSteps = study.process_steps ?? [];
  const characteristics = study.characteristics ?? [];
  const controlPlanItems = study.control_plan_items ?? [];
  const attachedPolicy = policies.find((item) => item.policy_key === study.action_priority_policy_key);
  const compatiblePolicies = policies.filter((item) => item.policy.standard_version === study.standard_version);
  const currentReport = report?.snapshot_digest === study.digest ? report : null;

  return (
    <div className="page fmea-page" data-density="compact">
      <Link className="back-link" to="/fmea"><ArrowLeft aria-hidden="true" /> FMEA 목록</Link>
      <section className="result-header">
        <div><span className="eyebrow">{study.study_type === "process" ? "PROCESS FMEA" : "DESIGN FMEA"}</span><h1>{study.name}</h1><p>{study.study_id} · {study.standard_version} · revision {study.revision}</p></div>
        <div className="result-actions"><span className={`status-badge status-${study.status}`}>{statusLabels[study.status]}</span>{study.status === "draft" && <><Button onClick={() => setShowForm((value) => !value)} icon={<FilePlus2 />}>{showForm ? "입력 닫기" : "고장 모드 추가"}</Button><Button onClick={() => setShowActionForm((value) => !value)} disabled={study.items.length === 0} icon={<Wrench />}>{showActionForm ? "조치 입력 닫기" : "권고조치 추가"}</Button><Button variant="primary" disabled={study.items.length === 0} loading={busy} onClick={handleSubmitReview} icon={<ClipboardCheck />}>검토 요청</Button></>}{study.status === "in_review" && <Button variant="primary" loading={busy} onClick={handleApprove} icon={<CheckCircle2 />}>승인</Button>}</div>
      </section>
      {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div>}

      <section className="panel" aria-labelledby="fmea-report-title">
        <header className="panel-heading"><div><span className="eyebrow">STUDY REPORT</span><h2 id="fmea-report-title">FMEA 검토 보고서</h2></div><Button type="button" loading={reportBusy} onClick={handleLoadReport}>현재 revision 보기</Button></header>
        {reportError && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{reportError}</p></div>}
        {reportBusy && <p role="status">보고서를 불러오는 중입니다.</p>}
        {!reportBusy && !currentReport && !reportError && <p>현재 Study revision의 위험 분석, 조치, Control Plan 연결과 감사 기록을 확인할 수 있습니다.</p>}
        {currentReport && <>
          <p>Revision {currentReport.revision} · 상태 {statusLabels[currentReport.status]} · 항목 {currentReport.rows.length}개 · 감사 이벤트 {currentReport.audit_events.length}건</p>
          <p>스냅샷 식별값: <code>{currentReport.snapshot_digest}</code></p>
          <p>{currentReport.approval_record ? `승인 기록: ${currentReport.approval_record.actor} · ${currentReport.approval_record.occurred_at}` : "승인 기록 없음"}</p>
          {currentReport.rows.length === 0 ? <p>보고할 고장 분석 항목이 없습니다.</p> : <div className="table-scroll"><table><caption>현재 revision의 FMEA 위험 분석과 공정관리 연결</caption><thead><tr><th scope="col">항목</th><th scope="col">고장 모드 · 원인</th><th scope="col">현재 S/O/D</th><th scope="col">AP</th><th scope="col">공정 단계 · 특성</th><th scope="col">Control Plan</th><th scope="col">조치</th></tr></thead><tbody>{currentReport.rows.map((row) => <tr key={row.failure.item_id}><th scope="row">{row.failure.item_id}</th><td>{row.failure.failure_mode}<span className="table-subtitle">{row.failure.cause}</span></td><td>{row.failure.current_ratings.severity} / {row.failure.current_ratings.occurrence} / {row.failure.current_ratings.detection}</td><td>{row.failure.action_priority ?? "미산정"}</td><td>{row.process_step?.step_id ?? "—"} · {row.characteristics.map((item) => item.characteristic_id).join(", ") || "—"}</td><td>{row.control_plan_items.map((item) => item.control_id).join(", ") || "—"}</td><td>{row.actions.map((item) => `${item.action_id} (${item.status})`).join(", ") || "—"}</td></tr>)}</tbody></table></div>}
          {currentReport.limitations.map((limitation) => <p key={limitation} className="policy-note">{limitation}</p>)}
        </>}
      </section>

      {study.seven_step_progress && <section className="panel seven-step-panel" aria-labelledby="seven-step-title">
        <header className="panel-heading"><div><span className="eyebrow">AIAG/VDA WORKFLOW</span><h2 id="seven-step-title">FMEA 7단계 진행</h2></div><span>실제 Study 증거에서 자동 산정</span></header>
        <ol className="seven-step-list">{study.seven_step_progress.map((step) => <li key={step.step_id} className={`step-${step.status}`}>
          <span className="step-number">{step.step_number}</span><div><strong>{stepTitles[step.step_id] ?? step.title}</strong><span>{stepStatusLabels[step.status]} · 증거 {step.evidence_count}건</span>{step.gaps.length > 0 && <small>남은 항목: {step.gaps.join(", ")}</small>}</div>
        </li>)}</ol>
      </section>}

      {study.study_type === "process" && <section className="panel traceability-panel" aria-labelledby="traceability-title">
        <header className="panel-heading"><div><span className="eyebrow">PROCESS LINKAGE</span><h2 id="traceability-title">공정흐름–PFMEA–Control Plan 추적</h2></div><GitBranch aria-hidden="true" /></header>
        {study.status === "draft" && <div className="traceability-actions" aria-label="추적 항목 추가">
          <Button type="button" onClick={() => setTraceEditor(traceEditor === "step" ? null : "step")}>공정 단계</Button>
          <Button type="button" onClick={() => setTraceEditor(traceEditor === "characteristic" ? null : "characteristic")} disabled={processSteps.length === 0}>공정 특성</Button>
          <Button type="button" onClick={() => setTraceEditor(traceEditor === "control" ? null : "control")} disabled={characteristics.length === 0 || study.items.length === 0}>Control Plan</Button>
        </div>}
        {traceEditor === "step" && <form className="traceability-form" onSubmit={handleAddProcessStep}>
          <label className="field">단계 ID<input name="step_id" required defaultValue={`STEP-${String((processSteps.length + 1) * 10).padStart(3, "0")}`} /></label>
          <label className="field">순서<input name="sequence" type="number" min="1" required defaultValue={(processSteps.length + 1) * 10} /></label>
          <label className="field">단계명<input name="name" required /></label>
          <label className="field field-wide">작업 내용<input name="operation" required /></label>
          <label className="field">작성자<input name="actor" required defaultValue="process.engineer" /></label>
          <div className="form-actions"><Button type="submit" loading={busy}>공정 단계 저장</Button></div>
        </form>}
        {traceEditor === "characteristic" && <form className="traceability-form" onSubmit={handleAddCharacteristic}>
          <label className="field">특성 ID<input name="characteristic_id" required defaultValue={`CHAR-${String(characteristics.length + 1).padStart(3, "0")}`} /></label>
          <label className="field">공정 단계<select name="process_step_id" required defaultValue=""><option value="" disabled>단계 선택</option>{processSteps.map((step) => <option key={step.step_id} value={step.step_id}>{step.sequence} · {step.name}</option>)}</select></label>
          <label className="field">특성 유형<select name="characteristic_type" required defaultValue="product"><option value="product">제품 특성</option><option value="process">공정 특성</option></select></label>
          <label className="field">특성명<input name="name" required /></label>
          <label className="field field-wide">규격 / 허용범위<input name="specification" required /></label>
          <label className="field">특별특성 분류<input name="special_classification" placeholder="예: SC, CC" /></label>
          <label className="field">작성자<input name="actor" required defaultValue="quality.engineer" /></label>
          <div className="form-actions"><Button type="submit" loading={busy}>공정 특성 저장</Button></div>
        </form>}
        {traceEditor === "control" && <form className="traceability-form" onSubmit={handleAddControlPlan}>
          <label className="field">관리 ID<input name="control_id" required defaultValue={`CP-${String(controlPlanItems.length + 1).padStart(3, "0")}`} /></label>
          <label className="field">단계<select name="phase" required defaultValue="production"><option value="prototype">Prototype</option><option value="pre_launch">Pre-launch</option><option value="production">Production</option><option value="safe_launch">Safe launch</option></select></label>
          <label className="field">공정 특성<select name="characteristic_id" required defaultValue=""><option value="" disabled>특성 선택</option>{characteristics.map((item) => <option key={item.characteristic_id} value={item.characteristic_id}>{item.characteristic_id} · {item.name}</option>)}</select></label>
          <label className="field">PFMEA 고장 분석<select name="failure_item_ids" required multiple size={Math.min(4, Math.max(2, study.items.length))}>{study.items.map((item) => <option key={item.item_id} value={item.item_id}>{item.item_id} · {item.failure_mode}</option>)}</select><small>Ctrl 키로 여러 항목 선택</small></label>
          <label className="field">측정 방법<input name="measurement_method" required /></label>
          <label className="field">표본 수<input name="sample_size" type="number" min="1" required defaultValue="1" /></label>
          <label className="field">주기<input name="frequency" required placeholder="예: 매 로트" /></label>
          <label className="field">관리 방법<input name="control_method" required placeholder="예: Xbar-R 관리도" /></label>
          <label className="field field-wide">반응 계획<textarea name="reaction_plan" required /></label>
          <label className="field">반응 책임자<input name="reaction_owner" required /></label>
          <label className="field">작성자<input name="actor" required defaultValue="quality.engineer" /></label>
          <div className="form-actions"><Button type="submit" loading={busy}>Control Plan 저장</Button></div>
        </form>}
        {processSteps.length === 0 ? <div className="state-message"><GitBranch aria-hidden="true" /><h3>공정흐름이 없습니다</h3><p>공정 단계를 먼저 등록하면 PFMEA와 Control Plan을 ID로 연결할 수 있습니다.</p></div> : <div className="table-scroll"><table className="traceability-table"><thead><tr><th>공정 단계</th><th>제품/공정 특성</th><th>PFMEA 고장 분석</th><th>Control Plan</th><th>관리·반응</th></tr></thead><tbody>{characteristics.length === 0 ? processSteps.map((step) => <tr key={step.step_id}><td><strong>{step.step_id}</strong><span className="table-subtitle">{step.sequence} · {step.name}</span></td><td colSpan={4}><span className="status-text is-muted">연결된 공정 특성 없음</span></td></tr>) : characteristics.map((characteristic) => {
            const step = processSteps.find((candidate) => candidate.step_id === characteristic.process_step_id);
            const failures = study.items.filter((item) => (item.characteristic_ids ?? []).includes(characteristic.characteristic_id));
            const controls = controlPlanItems.filter((item) => item.characteristic_id === characteristic.characteristic_id);
            return <tr key={characteristic.characteristic_id}><td><strong>{step?.step_id ?? characteristic.process_step_id}</strong><span className="table-subtitle">{step?.sequence} · {step?.name ?? "미확인 단계"}</span></td><td><strong>{characteristic.characteristic_id} · {characteristic.name}</strong><span className="table-subtitle">{characteristic.specification}{characteristic.special_classification ? ` · ${characteristic.special_classification}` : ""}</span></td><td>{failures.length > 0 ? failures.map((item) => item.item_id).join(", ") : <span className="status-text is-muted">미연결</span>}</td><td>{controls.length > 0 ? controls.map((item) => `${item.control_id} · ${item.phase}`).join(", ") : <span className="status-text is-muted">미연결</span>}</td><td>{controls.length > 0 ? controls.map((item) => `${item.control_method} / ${item.reaction_owner}`).join(", ") : "—"}</td></tr>;
          })}</tbody></table></div>}
      </section>}

      <section className="panel ap-policy-panel" aria-labelledby="ap-policy-title">
        <header className="panel-heading"><div><span className="eyebrow">AUTHORIZED POLICY</span><h2 id="ap-policy-title">Action Priority 정책</h2></div><ShieldAlert aria-hidden="true" /></header>
        <div className="ap-policy-grid">
          <article className="policy-status-card">
            <h3>Study 연결 상태</h3>
            {study.action_priority_policy_key ? <><p><strong>{study.action_priority_policy_id}</strong></p><p>{attachedPolicy?.policy.standard_version ?? study.standard_version} · 항목 {attachedPolicy?.policy.entries.length ?? "확인 불가"}개</p><code>{study.action_priority_policy_digest}</code></> : <p className="status-text is-muted">연결된 정책이 없어 AP는 미계산 상태입니다.</p>}
            {study.status === "draft" && !study.action_priority_policy_key && <form className="form-stack" onSubmit={handleAttachPolicy}>
              <label className="field">호환 정책<select name="policy_key" required defaultValue=""><option value="" disabled>정책 선택</option>{compatiblePolicies.map(({ policy_key, policy }) => <option key={policy_key} value={policy_key}>{policy.policy_id} · {policy.entries.length}개 항목</option>)}</select><small>Study 표준 버전과 정확히 일치하는 정책만 표시합니다.</small></label>
              <label className="field">연결 담당자<input name="actor" required defaultValue="quality.admin" /></label>
              <Button type="submit" loading={busy} disabled={compatiblePolicies.length === 0} icon={<Link2 />}>정책 연결</Button>
            </form>}
          </article>
          <form className="policy-import-form" onSubmit={handleImportPolicy}>
            <h3>외부 정책 가져오기</h3>
            <p>고객이 적법하게 제공한 판정 항목만 입력합니다. StatPro는 독점 AP 표를 기본 제공하지 않습니다.</p>
            <label className="field">정책 ID<input name="policy_id" required placeholder="customer-ap-matrix" /></label>
            <label className="field">표준 버전<input name="standard_version" required defaultValue={study.standard_version} /></label>
            <label className="field">S,O,D,우선순위<textarea name="entries" required placeholder={"8,4,5,H\n8,2,2,M"} /><small>쉼표·탭·세미콜론 구분, 한 줄에 한 조합</small></label>
            <Button type="submit" loading={busy} icon={<Upload />}>불변 정책으로 가져오기</Button>
          </form>
        </div>
      </section>

      {showForm && <form className="panel failure-form" onSubmit={handleAddFailure}>
        <header className="panel-heading"><div><span className="eyebrow">FAILURE ANALYSIS</span><h2>고장 모드 추가</h2></div><span>저장 시 새 revision 생성</span></header>
        <div className="failure-fields">
          <label className="field">항목 ID<input ref={itemIdRef} name="item_id" required defaultValue={`FA-${String(study.items.length + 1).padStart(3, "0")}`} /></label>
          <label className="field">구조 요소<input name="structure_element" required /></label>
          <label className="field">기능<input name="function" required /></label>
          <label className="field">요구사항<input name="requirement" required /></label>
          <label className="field">고장 모드<input name="failure_mode" required /></label>
          <label className="field">영향<input name="effect" required /></label>
          <label className="field">원인<input name="cause" required /></label>
          <label className="field">예방 관리<input name="prevention_control" required /></label>
          <label className="field">검출 관리<input name="detection_control" required /></label>
          {study.study_type === "process" && processSteps.length > 0 && <label className="field">공정 단계<select name="process_step_id" required defaultValue=""><option value="" disabled>단계 선택</option>{processSteps.map((step) => <option key={step.step_id} value={step.step_id}>{step.sequence} · {step.name}</option>)}</select></label>}
          {study.study_type === "process" && characteristics.length > 0 && <label className="field">공정 특성<select name="characteristic_ids" multiple size={Math.min(4, Math.max(2, characteristics.length))}>{characteristics.map((item) => <option key={item.characteristic_id} value={item.characteristic_id}>{item.characteristic_id} · {item.name}</option>)}</select><small>필요한 특성을 모두 선택</small></label>}
          <label className="field">심각도 S<input name="severity" type="number" min="1" max="10" required defaultValue="5" /></label>
          <label className="field">발생도 O<input name="occurrence" type="number" min="1" max="10" required defaultValue="5" /></label>
          <label className="field">검출도 D<input name="detection" type="number" min="1" max="10" required defaultValue="5" /></label>
          <label className="field">작성자<input name="actor" required defaultValue="quality.engineer" /></label>
        </div>
        <div className="form-actions"><Button type="submit" variant="primary" loading={busy} icon={<FilePlus2 />}>고장 분석 저장</Button></div>
      </form>}

      {showActionForm && <form className="panel failure-form" onSubmit={handleAddAction}>
        <header className="panel-heading"><div><span className="eyebrow">RECOMMENDED ACTION</span><h2>권고조치 추가</h2></div><span>저장 시 새 revision 생성</span></header>
        <div className="failure-fields">
          <label className="field">조치 ID<input name="action_id" required defaultValue={`ACT-${String(study.actions.length + 1).padStart(3, "0")}`} /></label>
          <label className="field">고장 분석<select name="item_id" required defaultValue={selectedId ?? study.items[0]?.item_id}>{study.items.map((item) => <option key={item.item_id} value={item.item_id}>{item.item_id} · {item.failure_mode}</option>)}</select></label>
          <label className="field field-wide">권고조치<textarea name="description" required /></label>
          <label className="field">담당자<input name="owner" required /></label>
          <label className="field">완료 예정일<input name="due_date" type="date" required /></label>
          <label className="field">작성자<input name="actor" required defaultValue="quality.engineer" /></label>
        </div>
        <div className="form-actions"><Button type="submit" variant="primary" loading={busy} icon={<Wrench />}>권고조치 저장</Button></div>
      </form>}

      <section className="fmea-workbench">
        <aside className="panel structure-panel"><header className="panel-heading"><div><span className="eyebrow">STRUCTURE</span><h2>구조 요소</h2></div></header>{study.items.length === 0 ? <div className="state-message"><ShieldAlert aria-hidden="true" /><h3>분석 항목이 없습니다</h3><p>첫 고장 모드를 추가하세요.</p></div> : <ul className="structure-list">{study.items.map((item) => <li key={item.item_id}><button type="button" className={item.item_id === selectedId ? "is-selected" : ""} onClick={() => setSelectedId(item.item_id)}><strong>{item.structure_element}</strong><span>{item.failure_mode}</span></button></li>)}</ul>}</aside>
        <article className="panel risk-panel"><header className="panel-heading"><div><span className="eyebrow">RISK TABLE</span><h2>고장 분석</h2></div><span>{study.items.length}개 항목</span></header><div className="table-scroll"><table><thead><tr><th>항목</th><th>고장 모드</th><th>S</th><th>O</th><th>D</th><th>RPN</th><th>AP</th></tr></thead><tbody>{study.items.map((item) => <RiskRow key={item.item_id} item={item} selected={item.item_id === selectedId} onSelect={() => setSelectedId(item.item_id)} />)}</tbody></table></div>{selected && <section className="failure-detail" aria-live="polite"><h3>{selected.failure_mode}</h3><dl><div><dt>영향</dt><dd>{selected.effect}</dd></div><div><dt>원인</dt><dd>{selected.cause}</dd></div><div><dt>예방 관리</dt><dd>{selected.prevention_control}</dd></div><div><dt>검출 관리</dt><dd>{selected.detection_control}</dd></div></dl></section>}</article>
      </section>
      <section className="panel action-panel"><header className="panel-heading"><div><span className="eyebrow">ACTION TRACKING</span><h2>권고조치</h2></div><span>{study.actions.length}개</span></header>
        {study.actions.length === 0 ? <div className="state-message"><Wrench aria-hidden="true" /><h3>등록된 권고조치가 없습니다</h3><p>위험 저감을 위한 조치와 담당자를 기록하세요.</p></div> : <div className="action-list">{study.actions.map((action) => <ActionCard
          key={action.action_id}
          action={action}
          item={study.items.find((candidate) => candidate.item_id === action.item_id)}
          editable={study.status === "draft"}
          expanded={completingActionId === action.action_id}
          busy={busy}
          onStart={() => setCompletingActionId(action.action_id)}
          onCancel={() => setCompletingActionId(null)}
          onComplete={(event) => handleCompleteAction(event, action)}
        />)}</div>}
      </section>
      <p className="policy-note"><ShieldAlert aria-hidden="true" /> Action Priority는 고객이 제공한 버전형 정책이 연결될 때만 계산합니다. 현재 RPN은 S×O×D 참고값입니다.</p>
    </div>
  );
}

function ActionCard({ action, item, editable, expanded, busy, onStart, onCancel, onComplete }: {
  action: RecommendedAction;
  item: FailureAnalysis | undefined;
  editable: boolean;
  expanded: boolean;
  busy: boolean;
  onStart: () => void;
  onCancel: () => void;
  onComplete: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const status = action.status === "complete" ? "완료" : action.status === "cancelled" ? "취소" : "진행 필요";
  return <article className="action-card">
    <header><div><strong>{action.action_id} · {action.description}</strong><span>{action.item_id} · 담당 {action.owner} · 기한 {action.due_date}</span></div><span className={`status-badge status-${action.status}`}>{status}</span></header>
    {action.result && <p><strong>결과:</strong> {action.result}</p>}
    {action.evidence_refs.length > 0 && <p><strong>증거:</strong> {action.evidence_refs.join(", ")}</p>}
    {editable && action.status !== "complete" && (expanded ? <form className="action-complete-form" onSubmit={onComplete}>
      <label className="field field-wide">실행 결과<textarea name="result" required /></label>
      <label className="field field-wide">증거 참조<textarea name="evidence_refs" placeholder="한 줄에 하나씩 입력" /></label>
      <label className="field">재평가 S<input name="severity" type="number" min="1" max="10" required defaultValue={item?.current_ratings.severity ?? 5} /></label>
      <label className="field">재평가 O<input name="occurrence" type="number" min="1" max="10" required defaultValue={item?.current_ratings.occurrence ?? 5} /></label>
      <label className="field">재평가 D<input name="detection" type="number" min="1" max="10" required defaultValue={item?.current_ratings.detection ?? 5} /></label>
      <label className="field">완료자<input name="actor" required defaultValue="quality.engineer" /></label>
      <div className="form-actions"><Button type="button" onClick={onCancel}>취소</Button><Button type="submit" variant="primary" loading={busy} icon={<CheckCircle2 />}>완료 저장</Button></div>
    </form> : <Button onClick={onStart} icon={<CheckCircle2 />}>완료 및 재평가</Button>)}
  </article>;
}

function RiskRow({ item, selected, onSelect }: { item: FailureAnalysis; selected: boolean; onSelect: () => void }) {
  return <tr className={selected ? "is-selected" : ""} onClick={onSelect}><td><button type="button" className="table-row-button" onClick={onSelect}>{item.item_id}</button></td><td>{item.failure_mode}</td><td>{item.current_ratings.severity}</td><td>{item.current_ratings.occurrence}</td><td>{item.current_ratings.detection}</td><td><strong>{item.current_ratings.rpn}</strong></td><td>{item.action_priority ?? <span className="status-text is-muted">미계산</span>}</td></tr>;
}

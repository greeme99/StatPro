import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, ClipboardCheck, FlaskConical, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { createDmaicProject, getDmaicPilotPlan, listDmaicProjects, saveDmaicPilotPlan } from "../api";
import type { DmaicDocumentReference, StoredDmaicPilotPlan, StoredDmaicProject } from "../types";

type PilotForm = {
  pilotType: "before_after" | "controlled_trial" | "doe_confirmation";
  scope: string; studyDesign: string; samplePlan: string; duration: string;
  successMetrics: string; stopCriteria: string; riskResponses: string; analysisRunIds: string; actor: string;
};

const initialForm: PilotForm = {
  pilotType: "before_after", scope: "", studyDesign: "", samplePlan: "", duration: "",
  successMetrics: "", stopCriteria: "", riskResponses: "", analysisRunIds: "", actor: "local-operator",
};
const sourceLabels: Record<string, string> = {
  solution_selection: "개선안 선정", root_cause_analysis: "근본원인 분석", problem_definition: "문제 정의",
  measurement_plan: "측정 계획", sipoc: "SIPOC 맵", project_charter: "프로젝트 헌장",
};
const pilotLabels = { before_after: "전·후 비교", controlled_trial: "대조군 비교", doe_confirmation: "DOE 확인 실험" };
function asLines(value: string) { return value.split("\n").map((item) => item.trim()).filter(Boolean); }

export function DmaicPilotPlanWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [form, setForm] = useState<PilotForm>(initialForm);
  const [saved, setSaved] = useState<StoredDmaicPilotPlan | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { void (async () => {
    try { const page = await listDmaicProjects(); setProjects(page.items); setSelected(page.items[0] ?? null); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 불러오지 못했습니다."); }
    finally { setLoading(false); }
  })(); }, []);

  const sources = selected ? [selected.project.solution_selection, selected.project.root_cause_analysis, selected.project.problem_definition, selected.project.measurement_plan, selected.project.sipoc, selected.project.charter].filter((item): item is DmaicDocumentReference => item !== null) : [];
  const update = <K extends keyof PilotForm>(key: K, value: PilotForm[K]) => setForm((current) => ({ ...current, [key]: value }));

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    try {
      const project = await createDmaicProject({ project_id: String(values.get("project_id")), title: String(values.get("title")), owner_ref: String(values.get("owner_ref")), sponsor_ref: null, department: null });
      setProjects((current) => [project, ...current]); setSelected(project); setShowCreate(false); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 만들지 못했습니다."); }
  }

  async function savePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    try {
      const project = await saveDmaicPilotPlan(selected.project_id, {
        expected_storage_version: selected.storage_version, pilot_type: form.pilotType, scope: form.scope,
        study_design: form.studyDesign, sample_plan: form.samplePlan, duration: form.duration,
        success_metrics: asLines(form.successMetrics), stop_criteria: asLines(form.stopCriteria),
        risk_responses: asLines(form.riskResponses), analysis_run_ids: asLines(form.analysisRunIds),
        actor: form.actor, occurred_at: new Date().toISOString(),
      });
      const reference = project.project.pilot_plan;
      if (reference === null) throw new Error("저장된 파일럿 계획 참조를 확인하지 못했습니다.");
      const document = await getDmaicPilotPlan(project.project_id, reference.document_id);
      setSaved(document); setSelected(project); setProjects((current) => current.map((item) => item.project_id === project.project_id ? project : item)); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "파일럿 계획을 저장하지 못했습니다."); }
  }

  return <div className="page dmaic-measure-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><span>개선 (Improve)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><FlaskConical aria-hidden="true" /></span><div><span className="eyebrow">IMPROVE · PILOT · VALIDATE</span><h1>파일럿 계획 (Pilot Plan)</h1><p>선정한 개선안을 안전한 범위에서 검증하기 위한 실험·시범 운영 계획과 중단 기준을 개정 이력으로 보존합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="파일럿 계획 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>데이터</strong><p>범위·표본 계획</p></div></li><li><span>3</span><div><strong>분석</strong><p>성공·중단 기준</p></div></li><li><span>4</span><div><strong>결과</strong><p>위험 대응 검토</p></div></li><li><span>5</span><div><strong>보고서</strong><p>계획 개정 보존</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>파일럿 계획은 개선안 선정 및 분석 근거에 연결됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { setSelected(projects.find((item) => item.project_id === event.target.value) ?? null); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((item) => <option key={item.project_id} value={item.project_id}>{item.project.title} ({item.project_id})</option>)}</select></label><button className="button button-secondary" type="button" onClick={() => setShowCreate((value) => !value)}>새 개선 프로젝트 만들기</button></div>
      {showCreate && <form className="check-sheet-form" onSubmit={createProject}><label>프로젝트 ID<input name="project_id" defaultValue={`pilot-${Date.now()}`} required /></label><label>프로젝트명<input name="title" placeholder="예: 조립 불량 개선" required /></label><label className="check-sheet-wide">책임자<input name="owner_ref" defaultValue="local-operator" required /></label><button className="primary-button" type="submit">프로젝트 만들기 <ArrowRight aria-hidden="true" /></button></form>}</section>
      {selected && <form className="tool-workspace-panel dmaic-measure-form" onSubmit={savePlan}><header><h2>2. 파일럿 설계와 안전 기준</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><p className="method-note"><strong>주의:</strong> 이 문서는 실행 전 파일럿 계획입니다. 승인, 실행 또는 성공을 의미하지 않습니다.</p><div className="check-sheet-form"><label>파일럿 유형<select value={form.pilotType} onChange={(event) => update("pilotType", event.target.value as PilotForm["pilotType"])}>{Object.entries(pilotLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>저장 담당자<input value={form.actor} onChange={(event) => update("actor", event.target.value)} required /></label><label className="check-sheet-wide">적용 범위<textarea value={form.scope} onChange={(event) => update("scope", event.target.value)} placeholder="공정, 설비, 제품군, 적용 제외 범위를 입력하세요." required /></label><label className="check-sheet-wide">시험·비교 설계<textarea value={form.studyDesign} onChange={(event) => update("studyDesign", event.target.value)} placeholder="전·후 비교, 대조군 또는 DOE 확인 설계를 입력하세요." required /></label><label>표본·수집 계획<textarea value={form.samplePlan} onChange={(event) => update("samplePlan", event.target.value)} placeholder="표본 수, 층화·블록, 수집 주기를 입력하세요." required /></label><label>예상 기간<input value={form.duration} onChange={(event) => update("duration", event.target.value)} placeholder="예: 2교대" required /></label><label>성공 기준 (한 줄에 하나)<textarea value={form.successMetrics} onChange={(event) => update("successMetrics", event.target.value)} placeholder="예: 불량률 1% 미만" required /></label><label>중단 기준 (한 줄에 하나)<textarea value={form.stopCriteria} onChange={(event) => update("stopCriteria", event.target.value)} placeholder="예: 안전 이상 발생" required /></label><label className="check-sheet-wide">위험 대응 (한 줄에 하나)<textarea value={form.riskResponses} onChange={(event) => update("riskResponses", event.target.value)} placeholder="예: 즉시 이전 조건으로 복원" required /></label><label className="check-sheet-wide">연결할 분석 실행 ID (선택, 한 줄에 하나)<textarea value={form.analysisRunIds} onChange={(event) => update("analysisRunIds", event.target.value)} placeholder="DOE 또는 SPC 실행의 run_id를 입력하면 서버가 결과 다이제스트를 재검증합니다." /></label></div>
        <section className="dmaic-evidence-section"><header><ClipboardCheck aria-hidden="true" /><div><h3>연결된 프로젝트 근거</h3><p>저장 시점의 문서 개정과 다이제스트를 자동으로 고정합니다.</p></div></header>{sources.length === 0 ? <div className="method-note"><Link to="/home/dmaic/improve/solution-selection">개선안 선정 작업공간</Link>에서 먼저 검증할 개선안을 기록하세요.</div> : <div className="dmaic-run-list">{sources.map((source) => <div key={source.document_id}><span><strong>{sourceLabels[source.document_type] ?? source.document_type}</strong><small>개정 {source.revision} · {source.digest.slice(0, 12)}</small></span></div>)}</div>}</section>
        <button className="primary-button" type="submit">파일럿 계획 저장 <ArrowRight aria-hidden="true" /></button>
      </form>}
      {!selected && !showCreate && <section className="tool-workspace-panel"><p className="method-note">파일럿 계획을 시작하려면 개선 프로젝트를 선택하거나 새 프로젝트를 만드세요.</p></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><CheckCircle2 aria-hidden="true" /><div><h2>파일럿 계획을 새 개정으로 저장했습니다</h2><p>문서 {saved.document_id} · 개정 {saved.pilot_plan.revision} · 프로젝트 문서 {saved.pilot_plan.source_documents.length}건 · 분석 근거 {saved.pilot_plan.analysis_evidence.length}건</p></div></section>}
      <section className="tool-next-actions" aria-label="파일럿 실행 준비 도구"><article><FlaskConical aria-hidden="true" /><div><h2>DOE 확인 실험 준비</h2><p>선정한 조건과 반응값을 실험계획법으로 검증합니다.</p><Link className="text-link" to="/doe">실험계획법 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ShieldAlert aria-hidden="true" /><div><h2>SPC 기준선 확인</h2><p>시범 운영 전후의 공정 안정성을 관리도로 비교합니다.</p><Link className="text-link" to="/spc">SPC 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ClipboardCheck aria-hidden="true" /><div><h2>개선안 선정 재검토</h2><p>파일럿 범위가 선정 근거와 일치하는지 검토합니다.</p><Link className="text-link" to="/home/dmaic/improve/solution-selection">개선안 선정 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

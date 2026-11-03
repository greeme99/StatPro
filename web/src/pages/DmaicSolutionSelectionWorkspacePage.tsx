import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, ClipboardCheck, FlaskConical, Lightbulb } from "lucide-react";
import { Link } from "react-router-dom";
import { createDmaicProject, getDmaicSolutionSelection, listDmaicProjects, saveDmaicSolutionSelection } from "../api";
import type { DmaicDocumentReference, StoredDmaicProject, StoredDmaicSolutionSelection } from "../types";

type SelectionForm = {
  problemStatement: string;
  candidateSolutions: string;
  selectedSolution: string;
  decisionRationale: string;
  validationPlan: string;
  analysisRunIds: string;
  actor: string;
};

const initialForm: SelectionForm = {
  problemStatement: "", candidateSolutions: "", selectedSolution: "", decisionRationale: "",
  validationPlan: "", analysisRunIds: "", actor: "local-operator",
};

const sourceLabels: Record<string, string> = {
  project_charter: "프로젝트 헌장", voice_of_customer: "고객의 소리(VOC)", sipoc: "SIPOC 맵",
  stakeholder_assessment: "이해관계자 분석", problem_definition: "문제 정의", measurement_plan: "측정 계획",
  root_cause_analysis: "근본원인 분석",
};

function asLines(value: string) { return value.split("\n").map((item) => item.trim()).filter(Boolean); }

export function DmaicSolutionSelectionWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [form, setForm] = useState<SelectionForm>(initialForm);
  const [saved, setSaved] = useState<StoredDmaicSolutionSelection | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try { const page = await listDmaicProjects(); setProjects(page.items); setSelected(page.items[0] ?? null); }
      catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 불러오지 못했습니다."); }
      finally { setLoading(false); }
    }
    void load();
  }, []);

  const sources = selected ? [selected.project.root_cause_analysis, selected.project.problem_definition, selected.project.measurement_plan, selected.project.sipoc, selected.project.charter].filter((item): item is DmaicDocumentReference => item !== null) : [];
  const candidates = asLines(form.candidateSolutions);

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    try {
      const project = await createDmaicProject({ project_id: String(values.get("project_id")), title: String(values.get("title")), owner_ref: String(values.get("owner_ref")), sponsor_ref: null, department: null });
      setProjects((current) => [project, ...current]); setSelected(project); setShowCreate(false); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 만들지 못했습니다."); }
  }

  async function saveSelection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    try {
      const project = await saveDmaicSolutionSelection(selected.project_id, {
        expected_storage_version: selected.storage_version, problem_statement: form.problemStatement,
        candidate_solutions: candidates, selected_solution: form.selectedSolution,
        decision_rationale: form.decisionRationale, validation_plan: form.validationPlan,
        analysis_run_ids: asLines(form.analysisRunIds), actor: form.actor, occurred_at: new Date().toISOString(),
      });
      const reference = project.project.solution_selection;
      if (reference === null) throw new Error("저장된 개선안 선정 참조를 확인하지 못했습니다.");
      const document = await getDmaicSolutionSelection(project.project_id, reference.document_id);
      setSaved(document); setSelected(project); setProjects((current) => current.map((item) => item.project_id === project.project_id ? project : item)); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "개선안 선정을 저장하지 못했습니다."); }
  }

  return <div className="page dmaic-measure-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><span>개선 (Improve)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><Lightbulb aria-hidden="true" /></span><div><span className="eyebrow">IMPROVE · SELECT · VALIDATE</span><h1>개선안 선정 (Solution Selection)</h1><p>검증된 근본원인을 바탕으로 개선안을 선택하고, DOE 실행 근거와 검증 계획을 프로젝트 기록으로 보존합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="개선안 선정 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>데이터</strong><p>개선안 후보 기록</p></div></li><li><span>3</span><div><strong>분석</strong><p>선정 근거 검토</p></div></li><li><span>4</span><div><strong>결과</strong><p>검증 계획 확정</p></div></li><li><span>5</span><div><strong>보고서</strong><p>개정 이력 보존</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>개선안 선정은 근본원인 분석과 연결된 의사결정 기록입니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { setSelected(projects.find((item) => item.project_id === event.target.value) ?? null); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((item) => <option key={item.project_id} value={item.project_id}>{item.project.title} ({item.project_id})</option>)}</select></label><button className="button button-secondary" type="button" onClick={() => setShowCreate((value) => !value)}>새 개선 프로젝트 만들기</button></div>
      {showCreate && <form className="check-sheet-form" onSubmit={createProject}><label>프로젝트 ID<input name="project_id" defaultValue={`improve-${Date.now()}`} required /></label><label>프로젝트명<input name="title" placeholder="예: 조립 불량 개선" required /></label><label className="check-sheet-wide">책임자<input name="owner_ref" defaultValue="local-operator" required /></label><button className="primary-button" type="submit">프로젝트 만들기 <ArrowRight aria-hidden="true" /></button></form>}</section>
      {selected && <form className="tool-workspace-panel dmaic-measure-form" onSubmit={saveSelection}><header><h2>2. 개선안 선정과 검증 계획</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label className="check-sheet-wide">해결할 문제<textarea value={form.problemStatement} onChange={(event) => setForm((current) => ({ ...current, problemStatement: event.target.value }))} placeholder="근본원인 분석에서 확정한 문제를 입력하세요." required /></label><label className="check-sheet-wide">개선안 후보 (한 줄에 하나)<textarea value={form.candidateSolutions} onChange={(event) => setForm((current) => ({ ...current, candidateSolutions: event.target.value, selectedSolution: "" }))} placeholder={"예: 체결 토크 작업표준 변경\n예: 지그 가이드 추가"} required /></label><label>선정한 개선안<select value={form.selectedSolution} onChange={(event) => setForm((current) => ({ ...current, selectedSolution: event.target.value }))} required><option value="">개선안 후보를 먼저 입력하세요</option>{candidates.map((candidate) => <option key={candidate} value={candidate}>{candidate}</option>)}</select></label><label>저장 담당자<input value={form.actor} onChange={(event) => setForm((current) => ({ ...current, actor: event.target.value }))} required /></label><label className="check-sheet-wide">선정 근거<textarea value={form.decisionRationale} onChange={(event) => setForm((current) => ({ ...current, decisionRationale: event.target.value }))} placeholder="효과, 위험, 비용, 실행 가능성 등 선정 근거를 기록하세요." required /></label><label className="check-sheet-wide">검증 계획<textarea value={form.validationPlan} onChange={(event) => setForm((current) => ({ ...current, validationPlan: event.target.value }))} placeholder="DOE 설계, 성공 기준, 확인할 반응값을 기록하세요." required /></label><label className="check-sheet-wide">연결할 분석 실행 ID (선택, 한 줄에 하나)<textarea value={form.analysisRunIds} onChange={(event) => setForm((current) => ({ ...current, analysisRunIds: event.target.value }))} placeholder="DOE 또는 SPC 분석 실행의 run_id를 입력하면 서버가 결과 다이제스트를 재검증합니다." /></label></div>
        <section className="dmaic-evidence-section"><header><ClipboardCheck aria-hidden="true" /><div><h3>연결된 프로젝트 근거</h3><p>저장 시점의 문서 개정과 다이제스트를 자동으로 고정합니다.</p></div></header>{sources.length === 0 ? <div className="method-note"><Link to="/home/dmaic/analyze/root-causes">근본원인 분석 작업공간</Link>에서 검증 원인을 먼저 기록하면 개선안 선정에 함께 연결됩니다.</div> : <div className="dmaic-run-list">{sources.map((source) => <div key={source.document_id}><span><strong>{sourceLabels[source.document_type] ?? source.document_type}</strong><small>개정 {source.revision} · {source.digest.slice(0, 12)}</small></span></div>)}</div>}</section>
        <button className="primary-button" type="submit">개선안 선정 저장 <ArrowRight aria-hidden="true" /></button>
      </form>}
      {!selected && !showCreate && <section className="tool-workspace-panel"><p className="method-note">개선안 선정을 시작하려면 개선 프로젝트를 선택하거나 새 프로젝트를 만드세요.</p></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><CheckCircle2 aria-hidden="true" /><div><h2>개선안 선정을 새 개정으로 저장했습니다</h2><p>문서 {saved.document_id} · 개정 {saved.solution_selection.revision} · 프로젝트 문서 {saved.solution_selection.source_documents.length}건 · 분석 근거 {saved.solution_selection.analysis_evidence.length}건</p></div></section>}
      <section className="tool-next-actions" aria-label="개선안 검증 도구"><article><FlaskConical aria-hidden="true" /><div><h2>DOE로 개선안 검증</h2><p>선정한 조건과 반응값을 실험계획법으로 검증합니다.</p><Link className="text-link" to="/doe">실험계획법 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ClipboardCheck aria-hidden="true" /><div><h2>근본원인 재확인</h2><p>개선안이 검증된 원인에 직접 대응하는지 검토합니다.</p><Link className="text-link" to="/home/dmaic/analyze/root-causes">근본원인 분석 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><CheckCircle2 aria-hidden="true" /><div><h2>관리 단계로 이관</h2><p>검증 결과는 SPC와 FMEA 관리계획으로 이어집니다.</p><Link className="text-link" to="/fmea">FMEA 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

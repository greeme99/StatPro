import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, ClipboardCheck, Search, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { createDmaicProject, getDmaicRootCauseAnalysis, listDmaicProjects, saveDmaicRootCauseAnalysis } from "../api";
import type { DmaicDocumentReference, StoredDmaicProject, StoredDmaicRootCauseAnalysis } from "../types";

type RootCauseForm = {
  problemStatement: string;
  method: "fishbone_pareto" | "five_whys" | "data_analysis";
  candidateCauses: string;
  verifiedCauses: string;
  nextActions: string;
  analysisRunIds: string;
  actor: string;
};

const initialForm: RootCauseForm = {
  problemStatement: "", method: "fishbone_pareto", candidateCauses: "", verifiedCauses: "", nextActions: "", analysisRunIds: "", actor: "local-operator",
};

const sourceLabels: Record<string, string> = {
  project_charter: "프로젝트 헌장", voice_of_customer: "고객의 소리(VOC)", sipoc: "SIPOC 맵",
  stakeholder_assessment: "이해관계자 분석", problem_definition: "문제 정의", measurement_plan: "측정 계획",
};

function asLines(value: string) { return value.split("\n").map((item) => item.trim()).filter(Boolean); }

export function DmaicRootCauseWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [form, setForm] = useState<RootCauseForm>(initialForm);
  const [saved, setSaved] = useState<StoredDmaicRootCauseAnalysis | null>(null);
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

  const sources = selected ? [selected.project.charter, selected.project.voice_of_customer, selected.project.sipoc, selected.project.stakeholder_assessment, selected.project.problem_definition, selected.project.measurement_plan].filter((item): item is DmaicDocumentReference => item !== null) : [];

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    try {
      const project = await createDmaicProject({ project_id: String(values.get("project_id")), title: String(values.get("title")), owner_ref: String(values.get("owner_ref")), sponsor_ref: null, department: null });
      setProjects((current) => [project, ...current]); setSelected(project); setShowCreate(false); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 만들지 못했습니다."); }
  }

  async function saveAnalysis(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    try {
      const project = await saveDmaicRootCauseAnalysis(selected.project_id, {
        expected_storage_version: selected.storage_version, problem_statement: form.problemStatement, method: form.method,
        candidate_causes: asLines(form.candidateCauses), verified_causes: asLines(form.verifiedCauses), next_actions: asLines(form.nextActions),
        analysis_run_ids: asLines(form.analysisRunIds), actor: form.actor, occurred_at: new Date().toISOString(),
      });
      const reference = project.project.root_cause_analysis;
      if (reference === null) throw new Error("저장된 근본원인 분석 참조를 확인하지 못했습니다.");
      const document = await getDmaicRootCauseAnalysis(project.project_id, reference.document_id);
      setSaved(document); setSelected(project); setProjects((current) => current.map((item) => item.project_id === project.project_id ? project : item)); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "근본원인 분석을 저장하지 못했습니다."); }
  }

  return <div className="page dmaic-measure-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><span>분석 (Analyze)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><Search aria-hidden="true" /></span><div><span className="eyebrow">ANALYZE · VERIFY · TRACE</span><h1>근본원인 분석 (Root Cause Analysis)</h1><p>특성요인도와 파레토의 조사 결과를 개선 프로젝트 문서에 고정하고, 검증 원인과 후속 조치를 추적합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="근본원인 분석 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>데이터</strong><p>문제·조사 근거 입력</p></div></li><li><span>3</span><div><strong>분석</strong><p>원인 후보 검증</p></div></li><li><span>4</span><div><strong>결과</strong><p>조치 항목 확정</p></div></li><li><span>5</span><div><strong>보고서</strong><p>개정 이력 보존</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>근본원인 분석은 프로젝트의 정의·측정 문서와 함께 저장됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { setSelected(projects.find((item) => item.project_id === event.target.value) ?? null); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((item) => <option key={item.project_id} value={item.project_id}>{item.project.title} ({item.project_id})</option>)}</select></label><button className="button button-secondary" type="button" onClick={() => setShowCreate((value) => !value)}>새 개선 프로젝트 만들기</button></div>
      {showCreate && <form className="check-sheet-form" onSubmit={createProject}><label>프로젝트 ID<input name="project_id" defaultValue={`analyze-${Date.now()}`} required /></label><label>프로젝트명<input name="title" placeholder="예: 조립 불량 원인 개선" required /></label><label className="check-sheet-wide">책임자<input name="owner_ref" defaultValue="local-operator" required /></label><button className="primary-button" type="submit">프로젝트 만들기 <ArrowRight aria-hidden="true" /></button></form>}</section>
      {selected && <form className="tool-workspace-panel dmaic-measure-form" onSubmit={saveAnalysis}><header><h2>2. 원인 조사와 검증</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label className="check-sheet-wide">문제 설명<textarea value={form.problemStatement} onChange={(event) => setForm((current) => ({ ...current, problemStatement: event.target.value }))} placeholder="확인하려는 현상과 범위를 구체적으로 기록하세요." required /></label><label>분석 방법<select value={form.method} onChange={(event) => setForm((current) => ({ ...current, method: event.target.value as RootCauseForm["method"] }))}><option value="fishbone_pareto">특성요인도 + 파레토</option><option value="five_whys">5 Why</option><option value="data_analysis">데이터 분석</option></select></label><label>저장 담당자<input value={form.actor} onChange={(event) => setForm((current) => ({ ...current, actor: event.target.value }))} required /></label><label className="check-sheet-wide">원인 후보 (한 줄에 하나)<textarea value={form.candidateCauses} onChange={(event) => setForm((current) => ({ ...current, candidateCauses: event.target.value }))} placeholder={"예: 작업자 교육 편차\n예: 설비 온도 변동"} required /></label><label className="check-sheet-wide">검증된 원인 (한 줄에 하나)<textarea value={form.verifiedCauses} onChange={(event) => setForm((current) => ({ ...current, verifiedCauses: event.target.value }))} placeholder="데이터 또는 현장 확인으로 검증된 원인만 기록하세요." required /></label><label className="check-sheet-wide">다음 조치 (한 줄에 하나)<textarea value={form.nextActions} onChange={(event) => setForm((current) => ({ ...current, nextActions: event.target.value }))} placeholder="책임과 완료 기준을 포함한 후속 조치를 기록하세요." required /></label><label className="check-sheet-wide">연결할 분석 실행 ID (선택, 한 줄에 하나)<textarea value={form.analysisRunIds} onChange={(event) => setForm((current) => ({ ...current, analysisRunIds: event.target.value }))} placeholder="분석 실행 결과의 run_id를 입력하면 서버가 결과 다이제스트를 재검증합니다." /></label></div>
        <section className="dmaic-evidence-section"><header><ClipboardCheck aria-hidden="true" /><div><h3>프로젝트 문서 근거</h3><p>저장 시점의 문서 개정과 다이제스트를 자동으로 고정합니다.</p></div></header>{sources.length === 0 ? <div className="method-note"><Link to="/home/dmaic/define">정의 (Define) 작업공간</Link>에서 문제·범위를 먼저 기록하면 분석 근거가 함께 연결됩니다.</div> : <div className="dmaic-run-list">{sources.map((source) => <div key={source.document_id}><span><strong>{sourceLabels[source.document_type] ?? source.document_type}</strong><small>개정 {source.revision} · {source.digest.slice(0, 12)}</small></span></div>)}</div>}</section>
        <button className="primary-button" type="submit">근본원인 분석 저장 <ArrowRight aria-hidden="true" /></button>
      </form>}
      {!selected && !showCreate && <section className="tool-workspace-panel"><p className="method-note">근본원인 분석을 시작하려면 개선 프로젝트를 선택하거나 새 프로젝트를 만드세요.</p></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><ClipboardCheck aria-hidden="true" /><div><h2>근본원인 분석을 새 개정으로 저장했습니다</h2><p>문서 {saved.document_id} · 개정 {saved.root_cause_analysis.revision} · 프로젝트 문서 {saved.root_cause_analysis.source_documents.length}건 · 분석 근거 {saved.root_cause_analysis.analysis_evidence.length}건</p></div></section>}
      <section className="tool-next-actions" aria-label="원인 조사 도구"><article><Search aria-hidden="true" /><div><h2>특성요인도 조사</h2><p>원인 범주를 구조화하고 현장 후보를 수집합니다.</p><Link className="text-link" to="/spc/tools/fishbone">특성요인도 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ClipboardCheck aria-hidden="true" /><div><h2>파레토 우선순위</h2><p>결함·원인 데이터를 기준으로 집중 영역을 정합니다.</p><Link className="text-link" to="/spc/tools/pareto-chart">파레토 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ShieldCheck aria-hidden="true" /><div><h2>위험 조치 연결</h2><p>검증된 원인은 FMEA의 예방·탐지 조치로 이어갑니다.</p><Link className="text-link" to="/fmea">FMEA 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

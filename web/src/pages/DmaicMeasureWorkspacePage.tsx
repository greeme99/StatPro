import { FormEvent, useEffect, useMemo, useState } from "react";
import { ArrowRight, BarChart3, ClipboardCheck, Database, FlaskConical, ShieldCheck } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { createDmaicProject, getDmaicMeasurementPlan, listDmaicProjects, listRuns, saveDmaicMeasurementPlan } from "../api";
import type { StoredDmaicMeasurementPlan, StoredDmaicProject, StoredRun } from "../types";

type PlanForm = {
  primaryMetric: string; baselineValue: string; targetValue: string; dataSource: string;
  collectionMethod: string; collectionFrequency: string; samplingMethod: string;
  populationSize: string; sampleSize: string; samplingRationale: string;
  measurementInstrument: string; measurementUnit: string; measurementPrecision: string;
  calibrationRequired: boolean; msaRequired: boolean; actor: string;
};

const initialPlan: PlanForm = {
  primaryMetric: "", baselineValue: "", targetValue: "", dataSource: "", collectionMethod: "현장 측정",
  collectionFrequency: "일별", samplingMethod: "무작위", populationSize: "", sampleSize: "",
  samplingRationale: "", measurementInstrument: "", measurementUnit: "", measurementPrecision: "",
  calibrationRequired: false, msaRequired: false, actor: "local-operator",
};

function nullableNumber(value: string): number | null { return value.trim() === "" ? null : Number(value); }

const defineDocumentLabels: Record<string, string> = {
  project_charter: "프로젝트 헌장",
  voice_of_customer: "고객의 소리(VOC)",
  sipoc: "SIPOC 맵",
  stakeholder_assessment: "이해관계자 분석",
  problem_definition: "문제 정의",
};

export function DmaicMeasureWorkspacePage() {
  const [search] = useSearchParams();
  const handoffRunId = search.get("analysisRunId");
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [runs, setRuns] = useState<StoredRun[]>([]);
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);
  const [plan, setPlan] = useState<PlanForm>(initialPlan);
  const [savedPlan, setSavedPlan] = useState<StoredDmaicMeasurementPlan | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [projectPage, runPage] = await Promise.all([listDmaicProjects(), listRuns(50)]);
        setProjects(projectPage.items);
        setRuns(runPage.items);
        if (handoffRunId && runPage.items.some((run) => run.run_id === handoffRunId)) setSelectedRuns([handoffRunId]);
        setSelected(projectPage.items[0] ?? null);
      } catch (cause) { setError(cause instanceof Error ? cause.message : "측정 작업공간을 불러오지 못했습니다."); }
      finally { setLoading(false); }
    }
    void load();
  }, [handoffRunId]);

  const selectedEvidence = useMemo(() => new Set(selectedRuns), [selectedRuns]);

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    try {
      const stored = await createDmaicProject({
        project_id: String(values.get("project_id")), title: String(values.get("title")), owner_ref: String(values.get("owner_ref")),
        sponsor_ref: String(values.get("sponsor_ref")) || null, department: String(values.get("department")) || null,
      });
      setProjects((current) => [stored, ...current]); setSelected(stored); setShowCreate(false); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 만들지 못했습니다."); }
  }

  async function savePlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    try {
      const savedProject = await saveDmaicMeasurementPlan(selected.project_id, {
        expected_storage_version: selected.storage_version, primary_metric: plan.primaryMetric,
        baseline_value: nullableNumber(plan.baselineValue), target_value: nullableNumber(plan.targetValue),
        data_source: plan.dataSource, collection_method: plan.collectionMethod, collection_frequency: plan.collectionFrequency,
        sampling_method: plan.samplingMethod, population_size: nullableNumber(plan.populationSize), sample_size: nullableNumber(plan.sampleSize),
        sampling_rationale: plan.samplingRationale || null, measurement_instrument: plan.measurementInstrument || null,
        measurement_unit: plan.measurementUnit || null, measurement_precision: plan.measurementPrecision || null,
        calibration_required: plan.calibrationRequired, msa_required: plan.msaRequired, analysis_run_ids: selectedRuns,
        actor: plan.actor, occurred_at: new Date().toISOString(),
      });
      const reference = savedProject.project.measurement_plan;
      if (reference === null) throw new Error("저장된 측정 계획 참조를 확인하지 못했습니다.");
      const storedPlan = await getDmaicMeasurementPlan(selected.project_id, reference.document_id);
      setSavedPlan(storedPlan); setSelected(savedProject);
      setProjects((current) => current.map((project) => project.project_id === savedProject.project_id ? savedProject : project));
      setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "측정 계획을 저장하지 못했습니다."); }
  }

  function updatePlan<K extends keyof PlanForm>(key: K, value: PlanForm[K]) { setPlan((current) => ({ ...current, [key]: value })); }

  return <div className="page dmaic-measure-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><span>측정 (Measure)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><ClipboardCheck aria-hidden="true" /></span><div><span className="eyebrow">MEASURE · PLAN · TRACE</span><h1>측정 (Measure) 작업공간</h1><p>측정 기준과 표본 계획을 고정하고, 이미 실행한 SPC·DOE 분석 결과를 불변 근거로 연결합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="측정 계획 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>데이터</strong><p>수집·표본 기준 정의</p></div></li><li><span>3</span><div><strong>분석</strong><p>실행 근거 연결</p></div></li><li><span>4</span><div><strong>결과</strong><p>기준·목표값 검토</p></div></li><li><span>5</span><div><strong>보고서</strong><p>개정 이력 보존</p></div></li></ol>
    {loading ? <p className="method-note">로컬 프로젝트와 분석 실행 결과를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>측정 계획은 하나의 개선 프로젝트에 귀속되며 저장할 때마다 새 개정이 생성됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { setSelected(projects.find((project) => project.project_id === event.target.value) ?? null); setSavedPlan(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project.title} ({project.project_id})</option>)}</select></label><button className="button button-secondary" type="button" onClick={() => setShowCreate((value) => !value)}>새 개선 프로젝트 만들기</button></div>
      {showCreate && <form className="check-sheet-form" onSubmit={createProject}><label>프로젝트 ID<input name="project_id" defaultValue={`measure-${Date.now()}`} required /></label><label>프로젝트명<input name="title" placeholder="예: 조립 불량률 개선" required /></label><label>책임자<input name="owner_ref" defaultValue="local-operator" required /></label><label>후원자<input name="sponsor_ref" /></label><label className="check-sheet-wide">부서<input name="department" placeholder="예: 제조기술팀" /></label><button className="primary-button" type="submit">프로젝트 만들기 <ArrowRight aria-hidden="true" /></button></form>}</section>
      {selected && <form className="tool-workspace-panel dmaic-measure-form" onSubmit={savePlan}><header><h2>2. 측정 계획 작성</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label>핵심 성과지표<input value={plan.primaryMetric} onChange={(event) => updatePlan("primaryMetric", event.target.value)} placeholder="예: 외관 불량률" required /></label><label>데이터 원천<input value={plan.dataSource} onChange={(event) => updatePlan("dataSource", event.target.value)} placeholder="예: 검사 시스템 CSV" required /></label><label>기준값<input type="number" step="any" value={plan.baselineValue} onChange={(event) => updatePlan("baselineValue", event.target.value)} /></label><label>목표값<input type="number" step="any" value={plan.targetValue} onChange={(event) => updatePlan("targetValue", event.target.value)} /></label><label>수집 방법<select value={plan.collectionMethod} onChange={(event) => updatePlan("collectionMethod", event.target.value)}><option>현장 측정</option><option>시스템 추출</option><option>수기 검사</option></select></label><label>수집 주기<select value={plan.collectionFrequency} onChange={(event) => updatePlan("collectionFrequency", event.target.value)}><option>일별</option><option>교대별</option><option>로트별</option><option>주별</option></select></label><label>표본추출 방법<select value={plan.samplingMethod} onChange={(event) => updatePlan("samplingMethod", event.target.value)}><option>무작위</option><option>층화</option><option>전수</option><option>연속</option></select></label><label>모집단 크기<input type="number" min="1" value={plan.populationSize} onChange={(event) => updatePlan("populationSize", event.target.value)} /></label><label>표본 크기<input type="number" min="1" value={plan.sampleSize} onChange={(event) => updatePlan("sampleSize", event.target.value)} /></label><label>측정 장비<input value={plan.measurementInstrument} onChange={(event) => updatePlan("measurementInstrument", event.target.value)} /></label><label>측정 단위<input value={plan.measurementUnit} onChange={(event) => updatePlan("measurementUnit", event.target.value)} placeholder="예: %, mm" /></label><label>측정 분해능<input value={plan.measurementPrecision} onChange={(event) => updatePlan("measurementPrecision", event.target.value)} placeholder="예: 0.01 mm" /></label><label className="check-sheet-wide">표본추출 근거<input value={plan.samplingRationale} onChange={(event) => updatePlan("samplingRationale", event.target.value)} placeholder="표본 크기와 추출 기준의 근거" /></label><label className="check-sheet-wide">저장 담당자<input value={plan.actor} onChange={(event) => updatePlan("actor", event.target.value)} required /></label><div className="dmaic-checkboxes check-sheet-wide"><label><input type="checkbox" checked={plan.calibrationRequired} onChange={(event) => updatePlan("calibrationRequired", event.target.checked)} /> 교정 필요</label><label><input type="checkbox" checked={plan.msaRequired} onChange={(event) => updatePlan("msaRequired", event.target.checked)} /> 측정시스템 분석(MSA) 필요</label></div></div>
        <section className="dmaic-evidence-section"><header><ClipboardCheck aria-hidden="true" /><div><h3>정의 단계 근거</h3><p>저장 시점의 프로젝트 문서 개정과 다이제스트를 측정 계획에 자동으로 고정합니다.</p></div></header>{[selected.project.charter, selected.project.voice_of_customer, selected.project.sipoc, selected.project.stakeholder_assessment, selected.project.problem_definition].filter((reference): reference is NonNullable<typeof reference> => reference !== null).length === 0 ? <div className="method-note">연결된 정의 문서가 없습니다. <Link to="/home/dmaic/define">정의 (Define) 작업공간</Link>에서 문제와 범위를 먼저 기록하세요.</div> : <div className="dmaic-run-list">{[selected.project.charter, selected.project.voice_of_customer, selected.project.sipoc, selected.project.stakeholder_assessment, selected.project.problem_definition].filter((reference): reference is NonNullable<typeof reference> => reference !== null).map((reference) => <div key={reference.document_id}><span><strong>{defineDocumentLabels[reference.document_type] ?? reference.document_type}</strong><small>개정 {reference.revision} · {reference.digest.slice(0, 12)}</small></span></div>)}</div>}</section>
        <section className="dmaic-evidence-section"><header><Database aria-hidden="true" /><div><h3>3. 분석 실행 근거</h3><p>선택한 실행 결과의 식별자와 결과 다이제스트를 저장 시점에 서버가 다시 검증합니다.</p></div></header>{handoffRunId && <p className="method-note">SPC 결과에서 전달된 실행 ID <strong>{handoffRunId}</strong>{selectedEvidence.has(handoffRunId) ? "를 선택했습니다." : "를 찾지 못했습니다. 실행 결과 목록을 새로고침한 뒤 다시 확인하세요."}</p>}{runs.length === 0 ? <div className="method-note">연결할 실행 결과가 없습니다. 먼저 <Link to="/spc">SPC 작업공간</Link> 또는 <Link to="/doe">DOE 작업공간</Link>에서 분석을 실행하세요.</div> : <div className="dmaic-run-list">{runs.map((run) => <label key={run.run_id}><input type="checkbox" checked={selectedEvidence.has(run.run_id)} onChange={(event) => setSelectedRuns((current) => event.target.checked ? [...current, run.run_id] : current.filter((id) => id !== run.run_id))} /><span><strong>{run.result.analysis_type}</strong><small>{run.run_id} · 엔진 {run.result.engine_version}</small></span></label>)}</div>}</section>
        <button className="primary-button" type="submit">측정 계획 저장 <ArrowRight aria-hidden="true" /></button>
      </form>}
      {!selected && !showCreate && <section className="tool-workspace-panel"><p className="method-note">측정 계획을 시작하려면 기존 개선 프로젝트를 선택하거나 새 프로젝트를 만드세요.</p></section>}
      {savedPlan && <section className="dmaic-save-confirmation" aria-live="polite"><ClipboardCheck aria-hidden="true" /><div><h2>측정 계획을 새 개정으로 저장했습니다</h2><p>문서 {savedPlan.document_id} · 개정 {savedPlan.measurement_plan.revision} · 정의 문서 {savedPlan.measurement_plan.source_documents.length}건 · 분석 근거 {savedPlan.measurement_plan.analysis_evidence.length}건</p></div></section>}
      <section className="tool-next-actions" aria-label="연계 작업공간"><article><BarChart3 aria-hidden="true" /><div><h2>공정 안정성 확인</h2><p>표본 수집 후 SPC 관리도로 특수원인 신호를 확인합니다.</p><Link className="text-link" to="/spc">SPC 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><FlaskConical aria-hidden="true" /><div><h2>개선안 검증</h2><p>원인이 정리되면 DOE로 인자 조합과 반응을 검증합니다.</p><Link className="text-link" to="/doe">DOE 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ShieldCheck aria-hidden="true" /><div><h2>관리 조치 연결</h2><p>위험과 조치 책임은 FMEA 관리계획으로 이어갑니다.</p><Link className="text-link" to="/fmea">FMEA 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

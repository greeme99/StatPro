import { FormEvent, useEffect, useMemo, useState } from "react";
import { Activity, ArrowRight, CheckCircle2, ClipboardCheck, ShieldCheck, Siren } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import {
  getDmaicControlHandoff,
  listDmaicProjects,
  listFmeaStudies,
  listRuns,
  saveDmaicControlHandoff,
} from "../api";
import { persistActiveProject, selectActiveProject } from "../projectContext";
import type {
  DmaicReactionPlanItem,
  StoredDmaicControlHandoff,
  StoredDmaicProject,
  StoredFmeaStudy,
  StoredRun,
} from "../types";

type ControlForm = {
  monitoringPlan: string;
  reviewFrequency: string;
  effectivenessCriteria: string;
  actor: string;
};

const initialForm: ControlForm = {
  monitoringPlan: "",
  reviewFrequency: "교대별",
  effectivenessCriteria: "",
  actor: "local-operator",
};

const emptyReaction = (): DmaicReactionPlanItem => ({
  trigger: "",
  action: "",
  owner_ref: "",
  escalation_ref: null,
  response_time: "즉시",
});

function asLines(value: string) {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function isControlEvidence(run: StoredRun) {
  return run.result.analysis_type.startsWith("spc.") || run.result.analysis_type.startsWith("capability.");
}

export function DmaicControlWorkspacePage() {
  const [search] = useSearchParams();
  const handedOffRunId = search.get("analysisRunId");
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<StoredDmaicProject | null>(null);
  const [studies, setStudies] = useState<StoredFmeaStudy[]>([]);
  const [selectedStudyId, setSelectedStudyId] = useState("");
  const [selectedControlIds, setSelectedControlIds] = useState<string[]>([]);
  const [runs, setRuns] = useState<StoredRun[]>([]);
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [form, setForm] = useState<ControlForm>(initialForm);
  const [reactions, setReactions] = useState<DmaicReactionPlanItem[]>([emptyReaction()]);
  const [saved, setSaved] = useState<StoredDmaicControlHandoff | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void (async () => {
      try {
        const [projectPage, studyPage, runPage] = await Promise.all([
          listDmaicProjects(), listFmeaStudies(), listRuns(100),
        ]);
        const controlRuns = runPage.items.filter(isControlEvidence);
        setProjects(projectPage.items);
        setSelectedProject(selectActiveProject(projectPage.items));
        setStudies(studyPage.items);
        setSelectedStudyId(studyPage.items[0]?.study_id ?? "");
        setRuns(controlRuns);
        if (handedOffRunId && controlRuns.some((run) => run.run_id === handedOffRunId)) {
          setSelectedRunIds([handedOffRunId]);
        }
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "관리 작업공간을 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    })();
  }, [handedOffRunId]);

  const selectedStudy = studies.find((item) => item.study_id === selectedStudyId) ?? null;
  const selectedControls = useMemo(() => new Set(selectedControlIds), [selectedControlIds]);
  const selectedRuns = useMemo(() => new Set(selectedRunIds), [selectedRunIds]);

  function updateForm<K extends keyof ControlForm>(key: K, value: ControlForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateReaction<K extends keyof DmaicReactionPlanItem>(index: number, key: K, value: DmaicReactionPlanItem[K]) {
    setReactions((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item));
  }

  async function saveHandoff(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProject || !selectedStudy) return;
    setSaving(true);
    try {
      const project = await saveDmaicControlHandoff(selectedProject.project_id, {
        expected_storage_version: selectedProject.storage_version,
        monitoring_plan: form.monitoringPlan,
        review_frequency: form.reviewFrequency,
        effectiveness_criteria: asLines(form.effectivenessCriteria),
        reaction_plans: reactions,
        fmea_study_id: selectedStudy.study_id,
        fmea_control_ids: selectedControlIds,
        analysis_run_ids: selectedRunIds,
        actor: form.actor,
        occurred_at: new Date().toISOString(),
      });
      const reference = project.project.control_handoff;
      if (reference === null) throw new Error("저장된 관리 인수인계 참조를 확인하지 못했습니다.");
      const document = await getDmaicControlHandoff(project.project_id, reference.document_id);
      setSaved(document);
      setSelectedProject(project);
      setProjects((current) => current.map((item) => item.project_id === project.project_id ? project : item));
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "관리 인수인계를 저장하지 못했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return <div className="page dmaic-measure-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><span>관리 (Control)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><ShieldCheck aria-hidden="true" /></span><div><span className="eyebrow">CONTROL · REACT · VERIFY</span><h1>관리 (Control) 인수인계 작업공간</h1><p>개선 결과를 FMEA 관리계획과 연결하고, SPC·공정능력 실행 근거로 유지 효과를 검증하는 운영 계약을 만듭니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="관리 인수인계 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>데이터</strong><p>FMEA 관리항목 연결</p></div></li><li><span>3</span><div><strong>분석</strong><p>SPC 효과 근거 선택</p></div></li><li><span>4</span><div><strong>결과</strong><p>반응계획 검토</p></div></li><li><span>5</span><div><strong>보고서</strong><p>불변 인수인계 저장</p></div></li></ol>
    {loading ? <p className="method-note">프로젝트, FMEA 및 관리 분석 실행을 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>파일럿 결과와 운영 관리 근거가 귀속될 프로젝트를 선택합니다.</p></header>{projects.length === 0 ? <p className="method-note">먼저 <Link to="/home/dmaic/define">정의 (Define) 작업공간</Link>에서 개선 프로젝트를 만드세요.</p> : <div className="dmaic-project-picker"><label>프로젝트<select value={selectedProject?.project_id ?? ""} onChange={(event) => { const project = projects.find((item) => item.project_id === event.target.value) ?? null; setSelectedProject(project); persistActiveProject(project); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((item) => <option key={item.project_id} value={item.project_id}>{item.project.title} ({item.project_id})</option>)}</select></label></div>}</section>
      {selectedProject && <form className="tool-workspace-panel dmaic-measure-form" onSubmit={saveHandoff}>
        <header><h2>2. 운영 관리계획과 효과 검증</h2><p><strong>{selectedProject.project.title}</strong> · 프로젝트 개정 {selectedProject.project.revision}</p></header>
        <p className="method-note"><strong>인수인계 원칙:</strong> 관리항목, 분석 결과, 반응 책임자를 함께 저장합니다. 저장은 승인이나 공정 안정성 보증을 의미하지 않습니다.</p>
        <div className="check-sheet-form"><label>모니터링 계획<textarea value={form.monitoringPlan} onChange={(event) => updateForm("monitoringPlan", event.target.value)} placeholder="측정 위치, 관리도, 표본, 담당자와 검토 방법을 입력하세요." required /></label><label>검토 주기<select value={form.reviewFrequency} onChange={(event) => updateForm("reviewFrequency", event.target.value)}><option>교대별</option><option>일별</option><option>주별</option><option>로트별</option><option>월별</option></select></label><label className="check-sheet-wide">효과 판정 기준 (한 줄에 하나)<textarea value={form.effectivenessCriteria} onChange={(event) => updateForm("effectivenessCriteria", event.target.value)} placeholder="예: 20개 부분군 동안 관리한계 이탈 없음&#10;예: Cpk 1.33 이상" required /></label><label className="check-sheet-wide">저장 담당자<input value={form.actor} onChange={(event) => updateForm("actor", event.target.value)} required /></label></div>
        <section className="dmaic-evidence-section"><header><ShieldCheck aria-hidden="true" /><div><h3>3. FMEA 관리계획 연결</h3><p>선택한 연구의 개정·다이제스트와 관리항목 ID를 저장 시점에 고정합니다.</p></div></header>{studies.length === 0 ? <p className="method-note">연결 가능한 FMEA가 없습니다. <Link to="/fmea">FMEA 작업공간</Link>에서 관리계획 항목을 먼저 만드세요.</p> : <><div className="dmaic-project-picker"><label>FMEA 연구<select value={selectedStudyId} onChange={(event) => { setSelectedStudyId(event.target.value); setSelectedControlIds([]); }}><option value="">FMEA 연구를 선택하세요</option>{studies.map((item) => <option key={item.study_id} value={item.study_id}>{item.study.name} ({item.study_id})</option>)}</select></label></div>{selectedStudy && (selectedStudy.study.control_plan_items.length === 0 ? <p className="method-note">선택한 FMEA에 관리계획 항목이 없습니다. <Link to={`/fmea/${selectedStudy.study_id}`}>관리계획 작성 화면 열기</Link></p> : <div className="dmaic-run-list">{selectedStudy.study.control_plan_items.map((item) => <label key={item.control_id}><input type="checkbox" checked={selectedControls.has(item.control_id)} onChange={(event) => setSelectedControlIds((current) => event.target.checked ? [...current, item.control_id] : current.filter((id) => id !== item.control_id))} /><span><strong>{item.control_id} · {item.control_method}</strong><small>{item.phase} · {item.frequency} · 책임 {item.reaction_owner}</small></span></label>)}</div>)}</>}</section>
        <section className="dmaic-evidence-section"><header><Activity aria-hidden="true" /><div><h3>4. SPC·공정능력 효과 근거</h3><p>관리 효과를 확인한 실행만 선택할 수 있으며 서버가 저장 직전에 유형과 다이제스트를 재검증합니다.</p></div></header>{handedOffRunId && <p className="method-note">결과 화면에서 전달된 실행 <strong>{handedOffRunId}</strong>{selectedRuns.has(handedOffRunId) ? "을 선택했습니다." : "은 관리 근거 유형이 아니거나 찾을 수 없습니다."}</p>}{runs.length === 0 ? <p className="method-note">연결 가능한 SPC·공정능력 실행이 없습니다. <Link to="/spc">SPC 작업공간</Link>에서 분석을 먼저 실행하세요.</p> : <div className="dmaic-run-list">{runs.map((run) => <label key={run.run_id}><input type="checkbox" checked={selectedRuns.has(run.run_id)} onChange={(event) => setSelectedRunIds((current) => event.target.checked ? [...current, run.run_id] : current.filter((id) => id !== run.run_id))} /><span><strong>{run.result.analysis_type}</strong><small>{run.run_id} · 엔진 {run.result.engine_version}</small></span></label>)}</div>}</section>
        <section className="dmaic-evidence-section"><header><Siren aria-hidden="true" /><div><h3>5. 이상 반응계획</h3><p>신호가 발생했을 때 실행할 조치, 책임자, 대응 시간을 명확히 합니다.</p></div></header>{reactions.map((reaction, index) => <div className="check-sheet-form dmaic-reaction-plan" key={index}><label>발동 조건<input value={reaction.trigger} onChange={(event) => updateReaction(index, "trigger", event.target.value)} placeholder="예: 관리한계 이탈 또는 규칙 1 발생" required /></label><label>조치<input value={reaction.action} onChange={(event) => updateReaction(index, "action", event.target.value)} placeholder="예: 설비 정지 후 원인 확인" required /></label><label>책임자<input value={reaction.owner_ref} onChange={(event) => updateReaction(index, "owner_ref", event.target.value)} required /></label><label>상위 보고 대상<input value={reaction.escalation_ref ?? ""} onChange={(event) => updateReaction(index, "escalation_ref", event.target.value || null)} /></label><label>대응 시간<input value={reaction.response_time} onChange={(event) => updateReaction(index, "response_time", event.target.value)} required /></label>{reactions.length > 1 && <button className="button button-secondary" type="button" onClick={() => setReactions((current) => current.filter((_, itemIndex) => itemIndex !== index))}>반응계획 삭제</button>}</div>)}<button className="button button-secondary" type="button" onClick={() => setReactions((current) => [...current, emptyReaction()])}>반응계획 추가</button></section>
        <button className="primary-button" type="submit" disabled={saving || selectedControlIds.length === 0 || selectedRunIds.length === 0}>{saving ? "저장 중…" : "관리 인수인계 저장"} <ArrowRight aria-hidden="true" /></button>
      </form>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><CheckCircle2 aria-hidden="true" /><div><h2>관리 인수인계를 새 개정으로 저장했습니다</h2><p>문서 {saved.document_id} · 개정 {saved.control_handoff.revision} · FMEA 관리항목 {saved.control_handoff.fmea_control_plan.control_ids.length}건 · 분석 근거 {saved.control_handoff.analysis_evidence.length}건</p></div></section>}
      <section className="tool-next-actions" aria-label="관리 운영 도구"><article><Activity aria-hidden="true" /><div><h2>관리도 재검증</h2><p>다음 검토 주기에 동일 조건으로 관리 상태를 다시 확인합니다.</p><Link className="text-link" to="/spc/control-charts">관리도 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ShieldCheck aria-hidden="true" /><div><h2>FMEA 개정 검토</h2><p>공정 또는 관리방법 변경 시 위험과 관리계획을 함께 개정합니다.</p><Link className="text-link" to="/fmea">FMEA 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ClipboardCheck aria-hidden="true" /><div><h2>품질 지표 모니터링</h2><p>검증된 실행 결과를 품질 대시보드 지표로 운영합니다.</p><Link className="text-link" to="/quality">품질 대시보드 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

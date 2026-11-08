import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, ClipboardCheck, Route } from "lucide-react";
import { Link } from "react-router-dom";
import { getDmaicImplementationPlan, listDmaicProjects, saveDmaicImplementationPlan } from "../api";
import { persistActiveProject, selectActiveProject } from "../projectContext";
import type { StoredDmaicImplementationPlan, StoredDmaicProject } from "../types";

type Phase = { phase_id: string; name: string; owner_ref: string; target_date: string; completion_criteria: string };

const blankPhase = (): Phase => ({ phase_id: "", name: "", owner_ref: "", target_date: "", completion_criteria: "" });
const asLines = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);

export function DmaicImplementationPlanWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [strategy, setStrategy] = useState("");
  const [phases, setPhases] = useState<Phase[]>([blankPhase()]);
  const [communicationPlan, setCommunicationPlan] = useState("");
  const [qualityPlan, setQualityPlan] = useState("");
  const [trainingPlan, setTrainingPlan] = useState("");
  const [completionCriteria, setCompletionCriteria] = useState("");
  const [actor, setActor] = useState("local-operator");
  const [saved, setSaved] = useState<StoredDmaicImplementationPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { void (async () => {
    try { const page = await listDmaicProjects(); setProjects(page.items); setSelected(selectActiveProject(page.items)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 불러오지 못했습니다."); }
    finally { setLoading(false); }
  })(); }, []);

  const updatePhase = (index: number, key: keyof Phase, value: string) => {
    setPhases((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item));
  };

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    try {
      const project = await saveDmaicImplementationPlan(selected.project_id, {
        expected_storage_version: selected.storage_version,
        strategy,
        phases: phases.map((phase) => ({
          ...phase,
          target_date: phase.target_date || null,
          completion_criteria: asLines(phase.completion_criteria),
        })),
        communication_plan: communicationPlan,
        quality_plan: qualityPlan,
        training_plan: trainingPlan,
        completion_criteria: asLines(completionCriteria),
        actor,
        occurred_at: new Date().toISOString(),
      });
      const reference = project.project.implementation_plan;
      if (!reference) throw new Error("저장된 실행계획 참조를 확인하지 못했습니다.");
      const document = await getDmaicImplementationPlan(project.project_id, reference.document_id);
      setSaved(document); setSelected(project); persistActiveProject(project);
      setProjects((items) => items.map((item) => item.project_id === project.project_id ? project : item)); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "실행계획을 저장하지 못했습니다."); }
  }

  return <div className="page dmaic-measure-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span>/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span>/</span><span>실행계획</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><Route aria-hidden="true" /></span><div><span className="eyebrow">IMPROVE · ROLLOUT · OWNERSHIP</span><h1>실행계획 (Implementation Plan)</h1><p>개선안을 현장에 도입하기 위한 단계·담당·소통·품질·교육·완료 기준을 프로젝트 개정으로 보존합니다.</p></div></section>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>개선안·파일럿·비용편익 문서가 저장 시점의 근거로 연결됩니다.</p></header><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { const project = projects.find((item) => item.project_id === event.target.value) ?? null; setSelected(project); persistActiveProject(project); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((item) => <option key={item.project_id} value={item.project_id}>{item.project.title} ({item.project_id})</option>)}</select></label></section>
      {selected ? <form className="tool-workspace-panel dmaic-measure-form" onSubmit={save}><header><h2>2. 도입 절차와 완료 기준</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label className="check-sheet-wide">실행 전략<textarea value={strategy} onChange={(event) => setStrategy(event.target.value)} placeholder="예: 파일럿 승인 후 교대조별 통제된 확산을 진행합니다." required /></label><label className="check-sheet-wide">소통 계획<textarea value={communicationPlan} onChange={(event) => setCommunicationPlan(event.target.value)} placeholder="대상·주기·채널·승인 책임자를 기록합니다." required /></label><label>품질 계획<textarea value={qualityPlan} onChange={(event) => setQualityPlan(event.target.value)} placeholder="관리계획·반응계획·검증 근거를 기록합니다." required /></label><label>교육 계획<textarea value={trainingPlan} onChange={(event) => setTrainingPlan(event.target.value)} placeholder="대상 역할·교육 내용·이수 확인을 기록합니다." required /></label><label className="check-sheet-wide">프로젝트 완료 기준 (한 줄에 하나)<textarea value={completionCriteria} onChange={(event) => setCompletionCriteria(event.target.value)} placeholder="예: 파일럿 승인 근거가 기록됨" required /></label><label>저장 담당자<input value={actor} onChange={(event) => setActor(event.target.value)} required /></label></div><section className="dmaic-evidence-section"><header><ClipboardCheck aria-hidden="true" /><div><h3>실행 단계</h3><p>각 단계에는 하나의 책임자와 검토 가능한 완료 기준을 지정합니다.</p></div></header><div className="check-sheet-form">{phases.map((phase, index) => <div className="check-sheet-wide" key={index}><label>단계 ID<input value={phase.phase_id} onChange={(event) => updatePhase(index, "phase_id", event.target.value)} placeholder="pilot" required /></label><label>단계명<input value={phase.name} onChange={(event) => updatePhase(index, "name", event.target.value)} placeholder="파일럿" required /></label><label>담당자<input value={phase.owner_ref} onChange={(event) => updatePhase(index, "owner_ref", event.target.value)} placeholder="line.supervisor" required /></label><label>목표일<input type="date" value={phase.target_date} onChange={(event) => updatePhase(index, "target_date", event.target.value)} /></label><label className="check-sheet-wide">완료 기준 (한 줄에 하나)<textarea value={phase.completion_criteria} onChange={(event) => updatePhase(index, "completion_criteria", event.target.value)} required /></label><button className="button button-secondary" type="button" onClick={() => setPhases((items) => items.length === 1 ? items : items.filter((_, itemIndex) => itemIndex !== index))} disabled={phases.length === 1}>단계 제거</button></div>)}</div><button className="button button-secondary" type="button" onClick={() => setPhases((items) => [...items, blankPhase()])}>단계 추가</button></section><p className="method-note"><strong>한계:</strong> 이 문서는 도입 계획과 책임을 기록합니다. 실제 교육 이수, 승인, 생산 전환 또는 효과 실현을 자동으로 판정하지 않습니다.</p><button className="primary-button" type="submit">실행계획 저장 <ArrowRight aria-hidden="true" /></button></form> : <section className="tool-workspace-panel"><p className="method-note">실행계획을 시작하려면 먼저 개선 프로젝트를 선택하세요.</p></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><CheckCircle2 aria-hidden="true" /><div><h2>실행계획을 새 개정으로 저장했습니다</h2><p>실행 단계 {saved.implementation_plan.phases.length}개 · 근거 문서 {saved.implementation_plan.source_documents.length}건 · 실제 실행 완료 여부는 현장 검토가 필요합니다.</p></div></section>}
      <section className="tool-next-actions"><article><ClipboardCheck aria-hidden="true" /><div><h2>관리 인수인계 준비</h2><p>완료 기준을 검토한 뒤 관리계획서와 SPC·공정능력 근거를 연결합니다.</p><Link className="text-link" to="/home/dmaic/control">관리 인수인계 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

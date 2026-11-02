import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, ClipboardList, Flag, MessageSquareText, ShieldCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { createDmaicProject, listDmaicProjects, saveDmaicCharter } from "../api";
import type { StoredDmaicProject } from "../types";

type CharterForm = {
  businessCase: string; problemStatement: string; scopeIn: string; scopeOut: string;
  successMetrics: string; teamRefs: string; budget: string; milestones: string;
  risks: string; constraints: string; actor: string;
};

const initialCharter: CharterForm = {
  businessCase: "", problemStatement: "", scopeIn: "", scopeOut: "", successMetrics: "",
  teamRefs: "", budget: "", milestones: "", risks: "", constraints: "", actor: "local-operator",
};

function listValue(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

export function DmaicDefineWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [charter, setCharter] = useState<CharterForm>(initialCharter);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState<StoredDmaicProject | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const page = await listDmaicProjects();
        setProjects(page.items);
        setSelected(page.items[0] ?? null);
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "개선 프로젝트를 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  function update<K extends keyof CharterForm>(key: K, value: CharterForm[K]) {
    setCharter((current) => ({ ...current, [key]: value }));
  }

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    try {
      const stored = await createDmaicProject({
        project_id: String(values.get("project_id")),
        title: String(values.get("title")),
        owner_ref: String(values.get("owner_ref")),
        sponsor_ref: String(values.get("sponsor_ref")) || null,
        department: String(values.get("department")) || null,
      });
      setProjects((current) => [stored, ...current]);
      setSelected(stored);
      setShowCreate(false);
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "개선 프로젝트를 만들지 못했습니다.");
    }
  }

  async function saveCharter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    try {
      const stored = await saveDmaicCharter(selected.project_id, {
        expected_storage_version: selected.storage_version,
        business_case: charter.businessCase,
        problem_statement: charter.problemStatement,
        scope_in: listValue(charter.scopeIn),
        scope_out: listValue(charter.scopeOut),
        success_metrics: listValue(charter.successMetrics),
        team_refs: listValue(charter.teamRefs),
        budget: charter.budget.trim() || null,
        milestones: listValue(charter.milestones),
        risk_refs: listValue(charter.risks),
        assumptions_constraints: listValue(charter.constraints),
        actor: charter.actor,
        occurred_at: new Date().toISOString(),
      });
      setProjects((current) => current.map((item) => item.project_id === stored.project_id ? stored : item));
      setSelected(stored);
      setSaved(stored);
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "프로젝트 헌장을 저장하지 못했습니다.");
    }
  }

  return <div className="page dmaic-define-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><span>정의 (Define)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><ClipboardList aria-hidden="true" /></span><div><span className="eyebrow">DEFINE · CHARTER · ALIGN</span><h1>정의 (Define) 작업공간</h1><p>현장 문제와 성공 기준을 프로젝트 헌장으로 고정해, 이후 측정·분석·개선 활동의 공통 기준으로 사용합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="프로젝트 헌장 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>업무 범위</strong><p>문제와 경계 정의</p></div></li><li><span>3</span><div><strong>실행 기준</strong><p>성과·팀·일정 합의</p></div></li><li><span>4</span><div><strong>위험 검토</strong><p>제약과 위험 기록</p></div></li><li><span>5</span><div><strong>보고서</strong><p>불변 개정 저장</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>프로젝트 헌장은 선택한 프로젝트에 새 개정으로 저장됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { setSelected(projects.find((project) => project.project_id === event.target.value) ?? null); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project.title} ({project.project_id})</option>)}</select></label><button className="button button-secondary" type="button" onClick={() => setShowCreate((value) => !value)}>새 개선 프로젝트 만들기</button></div>
      {showCreate && <form className="check-sheet-form" onSubmit={createProject}><label>프로젝트 ID<input name="project_id" defaultValue={`define-${Date.now()}`} required /></label><label>프로젝트명<input name="title" placeholder="예: 조립 불량률 개선" required /></label><label>책임자<input name="owner_ref" defaultValue="local-operator" required /></label><label>후원자<input name="sponsor_ref" /></label><label className="check-sheet-wide">부서<input name="department" placeholder="예: 제조기술팀" /></label><button className="primary-button" type="submit">프로젝트 만들기 <ArrowRight aria-hidden="true" /></button></form>}</section>
      {selected && <form className="tool-workspace-panel dmaic-define-form" onSubmit={saveCharter}><header><h2>2. 프로젝트 헌장 작성</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label className="check-sheet-wide">추진 배경<textarea value={charter.businessCase} onChange={(event) => update("businessCase", event.target.value)} placeholder="왜 이 개선 과제가 필요한지 적으세요." required /></label><label className="check-sheet-wide">문제 정의<textarea value={charter.problemStatement} onChange={(event) => update("problemStatement", event.target.value)} placeholder="관찰된 문제, 영향, 발생 조건을 구체적으로 적으세요." required /></label><label>범위 포함<textarea value={charter.scopeIn} onChange={(event) => update("scopeIn", event.target.value)} placeholder="한 줄에 하나씩 입력" required /></label><label>범위 제외<textarea value={charter.scopeOut} onChange={(event) => update("scopeOut", event.target.value)} placeholder="한 줄에 하나씩 입력" required /></label><label>성공지표<textarea value={charter.successMetrics} onChange={(event) => update("successMetrics", event.target.value)} placeholder="예: 외관 불량률 2% 이하" required /></label><label>프로젝트 팀<textarea value={charter.teamRefs} onChange={(event) => update("teamRefs", event.target.value)} placeholder="역할 또는 사용자 참조를 한 줄에 하나씩 입력" required /></label><label>주요 마일스톤<textarea value={charter.milestones} onChange={(event) => update("milestones", event.target.value)} placeholder="예: 기준선 확정 2026-11-30" required /></label><label>위험·이해관계자<textarea value={charter.risks} onChange={(event) => update("risks", event.target.value)} placeholder="위험 또는 관리 책임자를 한 줄에 하나씩 입력" required /></label><label>예산<input value={charter.budget} onChange={(event) => update("budget", event.target.value)} placeholder="예: 5,000,000 KRW" /></label><label>저장 담당자<input value={charter.actor} onChange={(event) => update("actor", event.target.value)} required /></label><label className="check-sheet-wide">가정·제약사항<textarea value={charter.constraints} onChange={(event) => update("constraints", event.target.value)} placeholder="한 줄에 하나씩 입력" required /></label></div><button className="primary-button" type="submit">프로젝트 헌장 저장 <ArrowRight aria-hidden="true" /></button></form>}
      {!selected && !showCreate && <section className="tool-workspace-panel"><p className="method-note">프로젝트 헌장을 시작하려면 기존 개선 프로젝트를 선택하거나 새 프로젝트를 만드세요.</p></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><Flag aria-hidden="true" /><div><h2>프로젝트 헌장을 새 개정으로 저장했습니다</h2><p>프로젝트 {saved.project_id} · 개정 {saved.project.revision} · 이후 단계에서 이 범위와 성공 기준을 참조합니다.</p></div></section>}
      <section className="tool-next-actions" aria-label="다음 작업"><article><MessageSquareText aria-hidden="true" /><div><h2>고객의 소리(VOC) 연결</h2><p>고객 요구사항과 현장 불편을 구조화해 문제 정의와 성공지표를 보강합니다.</p><Link className="text-link" to="/home/dmaic/voc">VOC 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><Users aria-hidden="true" /><div><h2>측정 계획으로 연결</h2><p>헌장의 성공지표를 기준으로 수집·표본·측정시스템 계획을 작성합니다.</p><Link className="text-link" to="/home/dmaic/measure">측정 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ShieldCheck aria-hidden="true" /><div><h2>위험 조치 연결</h2><p>위험과 책임이 구체화되면 FMEA 작업공간에서 관리 조치를 연결합니다.</p><Link className="text-link" to="/fmea">FMEA 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

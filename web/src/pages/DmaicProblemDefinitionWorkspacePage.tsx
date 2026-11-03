import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, CircleAlert, ClipboardCheck, Target, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";
import { listDmaicProjects, saveDmaicProblemDefinition } from "../api";
import type { StoredDmaicProject } from "../types";

type Priority = "low" | "medium" | "high";

type ProblemDefinitionForm = {
  problemStatement: string; impact: string; currentState: string; targetState: string;
  timeframe: string; locationScope: string; severity: Priority; urgency: Priority;
  objectives: string; actor: string;
};

const initialForm: ProblemDefinitionForm = {
  problemStatement: "", impact: "", currentState: "", targetState: "", timeframe: "",
  locationScope: "", severity: "medium", urgency: "medium", objectives: "", actor: "local-operator",
};

function lines(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function priorityLabel(value: Priority): string {
  return value === "high" ? "높음" : value === "medium" ? "보통" : "낮음";
}

export function DmaicProblemDefinitionWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [form, setForm] = useState<ProblemDefinitionForm>(initialForm);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState<StoredDmaicProject | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const page = await listDmaicProjects();
        setProjects(page.items); setSelected(page.items[0] ?? null);
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "개선 프로젝트를 불러오지 못했습니다.");
      } finally { setLoading(false); }
    }
    void load();
  }, []);

  function update<K extends keyof ProblemDefinitionForm>(key: K, value: ProblemDefinitionForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function saveDefinition(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    if (!lines(form.objectives).length) {
      setError("업무 목표를 한 개 이상 입력하세요."); return;
    }
    try {
      const stored = await saveDmaicProblemDefinition(selected.project_id, {
        expected_storage_version: selected.storage_version,
        problem_statement: form.problemStatement,
        impact: form.impact,
        current_state: form.currentState,
        target_state: form.targetState,
        timeframe: form.timeframe,
        location_scope: form.locationScope,
        severity: form.severity,
        urgency: form.urgency,
        objectives: lines(form.objectives),
        actor: form.actor,
        occurred_at: new Date().toISOString(),
      });
      setProjects((current) => current.map((item) => item.project_id === stored.project_id ? stored : item));
      setSelected(stored); setSaved(stored); setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "문제 정의를 저장하지 못했습니다.");
    }
  }

  return <div className="page dmaic-problem-definition-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic/define">정의 (Define)</Link><span aria-hidden="true">/</span><span>문제 정의 (Problem Definition)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><CircleAlert aria-hidden="true" /></span><div><span className="eyebrow">DEFINE · PROBLEM · ALIGN</span><h1>문제 정의 (Problem Definition) 작업공간</h1><p>관찰된 현상과 목표 상태, 현장 영향, 우선순위를 분리해 기록하고, 측정과 개선에서 검증할 업무 목표를 고정합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="문제 정의 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>현상</strong><p>문제와 영향 기록</p></div></li><li><span>3</span><div><strong>격차</strong><p>현재·목표 상태 비교</p></div></li><li><span>4</span><div><strong>우선순위</strong><p>심각도·긴급도 판단</p></div></li><li><span>5</span><div><strong>보고서</strong><p>불변 개정 저장</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>문제 정의는 선택한 프로젝트의 새 개정으로 보존됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { setSelected(projects.find((project) => project.project_id === event.target.value) ?? null); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project.title} ({project.project_id})</option>)}</select></label><Link className="button button-secondary" to="/home/dmaic/define">프로젝트 헌장 열기</Link></div></section>
      {selected ? <form className="tool-workspace-panel" onSubmit={saveDefinition}><header><h2>2. 현장 문제와 목표 상태 작성</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><aside className="method-note"><strong>선택 가이드</strong><p>원인이나 해결책을 먼저 확정하지 말고, 측정 가능한 현재 상태와 원하는 목표 상태를 분리해 작성하세요.</p></aside><div className="check-sheet-form"><label className="check-sheet-wide">문제 정의<textarea value={form.problemStatement} onChange={(event) => update("problemStatement", event.target.value)} placeholder="예: 조립 2공정의 삽입 불량률이 관리 목표를 초과합니다." required /></label><label>영향<textarea value={form.impact} onChange={(event) => update("impact", event.target.value)} placeholder="예: 재작업 증가, 납기 지연, 고객 불만" required /></label><label>대상 위치·범위<textarea value={form.locationScope} onChange={(event) => update("locationScope", event.target.value)} placeholder="예: 조립 2라인, 삽입 공정" required /></label><label>현재 상태<textarea value={form.currentState} onChange={(event) => update("currentState", event.target.value)} placeholder="예: 최근 4주 평균 불량률 6.5%" required /></label><label>목표 상태<textarea value={form.targetState} onChange={(event) => update("targetState", event.target.value)} placeholder="예: 불량률 2% 이하, 공정 안정화" required /></label><label>달성 시점<input value={form.timeframe} onChange={(event) => update("timeframe", event.target.value)} placeholder="예: 2026년 2분기 고객 심사 전" required /></label><label>심각도 (Severity)<select value={form.severity} onChange={(event) => update("severity", event.target.value as Priority)}>{(["low", "medium", "high"] as Priority[]).map((value) => <option key={value} value={value}>{priorityLabel(value)}</option>)}</select></label><label>긴급도 (Urgency)<select value={form.urgency} onChange={(event) => update("urgency", event.target.value as Priority)}>{(["low", "medium", "high"] as Priority[]).map((value) => <option key={value} value={value}>{priorityLabel(value)}</option>)}</select></label><label className="check-sheet-wide">업무 목표<textarea value={form.objectives} onChange={(event) => update("objectives", event.target.value)} placeholder="한 줄에 하나씩 입력\n예: 삽입 불량률을 2% 이하로 낮춘다." required /></label><label>저장 담당자<input value={form.actor} onChange={(event) => update("actor", event.target.value)} required /></label></div><button className="primary-button" type="submit">문제 정의 저장 <ArrowRight aria-hidden="true" /></button></form> : <section className="tool-workspace-panel"><p className="method-note">문제 정의를 시작하려면 먼저 정의 작업공간에서 개선 프로젝트를 만드세요.</p><Link className="text-link" to="/home/dmaic/define">정의 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><ClipboardCheck aria-hidden="true" /><div><h2>문제 정의를 새 개정으로 저장했습니다</h2><p>프로젝트 {saved.project_id} · 개정 {saved.project.revision} · 현재 상태와 목표 상태가 이후 측정·분석의 검증 기준으로 연결됩니다.</p></div></section>}
      <section className="tool-next-actions" aria-label="다음 작업"><article><UsersRound aria-hidden="true" /><div><h2>이해관계자 분석 연결</h2><p>문제의 영향과 해결 과정에 참여하는 현장 책임자, 승인자, 지원 부서를 정리합니다.</p><Link className="text-link" to="/home/dmaic/stakeholders">이해관계자 분석 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><Target aria-hidden="true" /><div><h2>측정 계획 연결</h2><p>현재 상태와 목표 상태를 기준으로 데이터 수집, 표본, 측정시스템 확인 계획을 수립합니다.</p><Link className="text-link" to="/home/dmaic/measure">측정 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

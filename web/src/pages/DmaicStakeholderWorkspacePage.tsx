import { FormEvent, useEffect, useMemo, useState } from "react";
import { ArrowRight, ClipboardCheck, MessageSquareText, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";
import { listDmaicProjects, saveDmaicStakeholderAssessment } from "../api";
import { persistActiveProject, selectActiveProject } from "../projectContext";
import type { StoredDmaicProject } from "../types";

type StakeholderDraft = {
  name: string; role: string; department: string; influence: number; interest: number;
  attitude: "supportive" | "neutral" | "resistant";
  communication: "low" | "medium" | "high";
  concerns: string; expectations: string;
};

const initialDraft: StakeholderDraft = {
  name: "", role: "", department: "", influence: 3, interest: 3,
  attitude: "neutral", communication: "medium", concerns: "", expectations: "",
};

function asLines(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

function levelLabel(level: number): string {
  return level >= 4 ? "높음" : level <= 2 ? "낮음" : "보통";
}

export function DmaicStakeholderWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [draft, setDraft] = useState<StakeholderDraft>(initialDraft);
  const [stakeholders, setStakeholders] = useState<StakeholderDraft[]>([]);
  const [actor, setActor] = useState("local-operator");
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState<StoredDmaicProject | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const page = await listDmaicProjects();
        setProjects(page.items); setSelected(selectActiveProject(page.items));
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "개선 프로젝트를 불러오지 못했습니다.");
      } finally { setLoading(false); }
    }
    void load();
  }, []);

  const summary = useMemo(() => ({
    highInfluence: stakeholders.filter((item) => item.influence >= 4).length,
    activePartners: stakeholders.filter((item) => item.attitude === "supportive").length,
  }), [stakeholders]);

  function update<K extends keyof StakeholderDraft>(key: K, value: StakeholderDraft[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function addStakeholder() {
    if (!draft.name.trim() || !draft.role.trim()) {
      setError("이해관계자 이름과 역할을 입력하세요."); return;
    }
    setStakeholders((current) => [...current, draft]);
    setDraft(initialDraft); setError("");
  }

  async function saveAssessment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    if (!stakeholders.length) {
      setError("저장하려면 하나 이상의 이해관계자를 추가하세요."); return;
    }
    try {
      const stored = await saveDmaicStakeholderAssessment(selected.project_id, {
        expected_storage_version: selected.storage_version,
        stakeholders: stakeholders.map((item, index) => ({
          stakeholder_id: `stakeholder-${index + 1}`,
          name: item.name, role: item.role, department: item.department.trim() || null,
          influence: item.influence, interest: item.interest, attitude: item.attitude,
          communication: item.communication, concerns: asLines(item.concerns), expectations: asLines(item.expectations),
        })),
        actor, occurred_at: new Date().toISOString(),
      });
      setProjects((current) => current.map((item) => item.project_id === stored.project_id ? stored : item));
      setSelected(stored); setSaved(stored); setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "이해관계자 분석을 저장하지 못했습니다.");
    }
  }

  return <div className="page dmaic-stakeholder-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic/define">정의 (Define)</Link><span aria-hidden="true">/</span><span>이해관계자 분석 (Stakeholder Assessment)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><UsersRound aria-hidden="true" /></span><div><span className="eyebrow">DEFINE · STAKEHOLDER · ENGAGE</span><h1>이해관계자 분석 (Stakeholder Assessment) 작업공간</h1><p>프로젝트에 영향을 주거나 영향을 받는 사람의 관심도·영향도·소통 계획을 명시해, 실행 단계의 책임과 협업 방식을 정리합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="이해관계자 분석 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>식별</strong><p>역할과 부서 기록</p></div></li><li><span>3</span><div><strong>평가</strong><p>영향도·관심도 평가</p></div></li><li><span>4</span><div><strong>소통</strong><p>우려와 기대 관리</p></div></li><li><span>5</span><div><strong>보고서</strong><p>불변 개정 저장</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>이해관계자 분석은 선택한 프로젝트의 새 개정으로 보존됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { const project = projects.find((item) => item.project_id === event.target.value) ?? null; setSelected(project); persistActiveProject(project); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project.title} ({project.project_id})</option>)}</select></label><Link className="button button-secondary" to="/home/dmaic/define">프로젝트 헌장 열기</Link></div></section>
      {selected ? <form className="tool-workspace-panel" onSubmit={saveAssessment}><header><h2>2. 이해관계자 등록 및 소통 계획</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label>이름<input value={draft.name} onChange={(event) => update("name", event.target.value)} placeholder="예: 생산관리 책임자" /></label><label>역할<input value={draft.role} onChange={(event) => update("role", event.target.value)} placeholder="예: 공정 승인 및 자원 조정" /></label><label>부서<input value={draft.department} onChange={(event) => update("department", event.target.value)} placeholder="예: 생산관리팀" /></label><label>영향도 (Influence)<select value={draft.influence} onChange={(event) => update("influence", Number(event.target.value))}>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value} · {levelLabel(value)}</option>)}</select></label><label>관심도 (Interest)<select value={draft.interest} onChange={(event) => update("interest", Number(event.target.value))}>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value} · {levelLabel(value)}</option>)}</select></label><label>태도 (Attitude)<select value={draft.attitude} onChange={(event) => update("attitude", event.target.value as StakeholderDraft["attitude"])}><option value="supportive">지지</option><option value="neutral">중립</option><option value="resistant">우려</option></select></label><label>소통 수준 (Communication)<select value={draft.communication} onChange={(event) => update("communication", event.target.value as StakeholderDraft["communication"])}><option value="low">낮음</option><option value="medium">보통</option><option value="high">높음</option></select></label><label>주요 우려사항<textarea value={draft.concerns} onChange={(event) => update("concerns", event.target.value)} placeholder="한 줄에 하나씩 입력" /></label><label>기대사항<textarea value={draft.expectations} onChange={(event) => update("expectations", event.target.value)} placeholder="한 줄에 하나씩 입력" /></label></div><button className="button button-secondary" type="button" onClick={addStakeholder}>이해관계자 추가</button>
        <section className="dmaic-stakeholder-summary" aria-label="이해관계자 요약"><h3>등록 현황</h3><p>전체 {stakeholders.length}명 · 높은 영향도 {summary.highInfluence}명 · 지지 관계자 {summary.activePartners}명</p>{stakeholders.length ? <div className="spc-check-sheet-table-wrap"><table><thead><tr><th>이름</th><th>역할</th><th>영향도</th><th>관심도</th><th>태도</th><th>소통</th><th>삭제</th></tr></thead><tbody>{stakeholders.map((item, index) => <tr key={`${item.name}-${index}`}><td>{item.name}</td><td>{item.role}</td><td>{item.influence}</td><td>{item.interest}</td><td>{item.attitude === "supportive" ? "지지" : item.attitude === "neutral" ? "중립" : "우려"}</td><td>{item.communication === "high" ? "높음" : item.communication === "medium" ? "보통" : "낮음"}</td><td><button className="text-link" type="button" onClick={() => setStakeholders((current) => current.filter((_, currentIndex) => currentIndex !== index))}>제거</button></td></tr>)}</tbody></table></div> : <p className="method-note">이름과 역할을 입력한 뒤 이해관계자를 추가하세요.</p>}</section><label className="dmaic-actor-field">저장 담당자<input value={actor} onChange={(event) => setActor(event.target.value)} required /></label><button className="primary-button" type="submit">이해관계자 분석 저장 <ArrowRight aria-hidden="true" /></button></form> : <section className="tool-workspace-panel"><p className="method-note">이해관계자 분석을 시작하려면 먼저 정의 작업공간에서 개선 프로젝트를 만드세요.</p><Link className="text-link" to="/home/dmaic/define">정의 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><ClipboardCheck aria-hidden="true" /><div><h2>이해관계자 분석을 새 개정으로 저장했습니다</h2><p>프로젝트 {saved.project_id} · 개정 {saved.project.revision} · 이후 측정·개선·관리 단계의 책임 및 소통 근거로 참조할 수 있습니다.</p></div></section>}
      <section className="tool-next-actions" aria-label="다음 작업"><article><MessageSquareText aria-hidden="true" /><div><h2>고객의 소리(VOC) 연결</h2><p>핵심 이해관계자의 요구와 불편을 고객의 소리 항목으로 구조화합니다.</p><Link className="text-link" to="/home/dmaic/voc">VOC 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ClipboardCheck aria-hidden="true" /><div><h2>SIPOC 공정 맵 연결</h2><p>공정 책임자와 공급자·고객의 관점을 SIPOC 공정 경계에 반영합니다.</p><Link className="text-link" to="/home/dmaic/sipoc">SIPOC 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

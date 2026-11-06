import { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, CircleDashed, FileCheck2, FolderKanban, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { listDmaicProjects } from "../api";
import { persistActiveProject, selectActiveProject } from "../projectContext";
import type { DmaicDocumentReference, StoredDmaicProject } from "../types";

type EvidenceItem = {
  key: keyof StoredDmaicProject["project"];
  label: string;
  phase: string;
  to: string;
  reference: DmaicDocumentReference | null;
};

const phaseActions = [
  { phase: "정의 (Define)", description: "문제·고객·공정 경계와 책임을 합의합니다.", to: "/home/dmaic/define" },
  { phase: "측정 (Measure)", description: "기준선과 측정 신뢰성, 수집 계획을 확정합니다.", to: "/home/dmaic/measure" },
  { phase: "분석 (Analyze)", description: "검증 가능한 분석 근거로 핵심 원인을 좁힙니다.", to: "/home/dmaic/analyze/root-causes" },
  { phase: "개선 (Improve)", description: "대안을 비교하고 파일럿·DOE로 효과를 검증합니다.", to: "/home/dmaic/improve/solution-selection" },
  { phase: "관리 (Control)", description: "FMEA·SPC 근거와 반응계획을 운영으로 인계합니다.", to: "/home/dmaic/control" },
] as const;

function evidenceFor(stored: StoredDmaicProject): EvidenceItem[] {
  const project = stored.project;
  return [
    { key: "charter", label: "프로젝트 헌장", phase: "정의", to: "/home/dmaic/define", reference: project.charter },
    { key: "voice_of_customer", label: "고객의 소리 (VOC)", phase: "정의", to: "/home/dmaic/voc", reference: project.voice_of_customer },
    { key: "sipoc", label: "SIPOC 공정 맵", phase: "정의", to: "/home/dmaic/sipoc", reference: project.sipoc },
    { key: "stakeholder_assessment", label: "이해관계자 분석", phase: "정의", to: "/home/dmaic/stakeholders", reference: project.stakeholder_assessment },
    { key: "problem_definition", label: "문제 정의", phase: "정의", to: "/home/dmaic/problem-definition", reference: project.problem_definition },
    { key: "measurement_plan", label: "측정 계획", phase: "측정", to: "/home/dmaic/measure", reference: project.measurement_plan },
    { key: "root_cause_analysis", label: "근본원인 분석", phase: "분석", to: "/home/dmaic/analyze/root-causes", reference: project.root_cause_analysis },
    { key: "solution_selection", label: "개선안 선정", phase: "개선", to: "/home/dmaic/improve/solution-selection", reference: project.solution_selection },
    { key: "pilot_plan", label: "파일럿 계획", phase: "개선", to: "/home/dmaic/improve/pilot-plan", reference: project.pilot_plan },
    { key: "control_handoff", label: "관리 인수인계", phase: "관리", to: "/home/dmaic/control", reference: project.control_handoff },
  ];
}

export function DmaicProjectOverviewPage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    listDmaicProjects(50)
      .then((page) => {
        if (!active) return;
        const items = Array.isArray(page.items) ? page.items : [];
        setProjects(items);
        setSelected(selectActiveProject(items));
      })
      .catch((cause: Error) => { if (active) setError(cause.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const evidence = useMemo(() => selected ? evidenceFor(selected) : [], [selected]);
  const completed = evidence.filter((item) => item.reference !== null).length;
  const completion = evidence.length > 0 ? Math.round((completed / evidence.length) * 100) : 0;
  const nextEvidence = evidence.find((item) => item.reference === null) ?? null;

  function changeProject(projectId: string) {
    const project = projects.find((item) => item.project_id === projectId) ?? null;
    setSelected(project);
    persistActiveProject(project);
  }

  return <div className="page dmaic-project-overview" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><span>프로젝트 현황</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><FolderKanban aria-hidden="true" /></span><div><span className="eyebrow">PROJECT · EVIDENCE · HANDOFF</span><h1>현재 프로젝트 현황</h1><p>DMAIC 단계별 문서와 분석 연결 상태를 한 흐름에서 확인하고, 비어 있는 다음 현장 작업으로 바로 이동합니다.</p></div></section>

    {loading && <section className="workspace-section" aria-live="polite"><p className="method-note">개선 프로젝트 근거를 불러오고 있습니다.</p></section>}
    {error && <p className="error" role="alert">{error}</p>}
    {!loading && !error && projects.length === 0 && <section className="workspace-section dmaic-project-empty"><CircleDashed aria-hidden="true" /><div><h2>등록된 개선 프로젝트가 없습니다</h2><p>정의 작업공간에서 프로젝트를 만들고 헌장을 저장하면 단계별 근거가 이 화면에 누적됩니다.</p><Link className="button button-primary" to="/home/dmaic/define">프로젝트 만들기 <ArrowRight aria-hidden="true" /></Link></div></section>}

    {selected && <>
      <section className="dmaic-project-summary" aria-labelledby="project-summary-title">
        <div><span className="eyebrow">ACTIVE PROJECT</span><h2 id="project-summary-title">{selected.project.title}</h2><p>{selected.project_id} · Revision {selected.project.revision} · {selected.project.status}</p></div>
        <label>현재 프로젝트<select value={selected.project_id} onChange={(event) => changeProject(event.target.value)}>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project.title}</option>)}</select></label>
        <dl><div><dt>책임자</dt><dd>{selected.project.owner_ref}</dd></div><div><dt>부서</dt><dd>{selected.project.department || "미지정"}</dd></div><div><dt>목표일</dt><dd>{selected.project.target_end_date || "미지정"}</dd></div><div><dt>근거 완성도</dt><dd>{completed}/{evidence.length} · {completion}%</dd></div></dl>
        <div className="dmaic-project-progress" role="progressbar" aria-label="프로젝트 근거 완성도" aria-valuemin={0} aria-valuemax={100} aria-valuenow={completion}><span style={{ width: `${completion}%` }} /></div>
      </section>

      <section className="dmaic-project-phases" aria-labelledby="phase-progress-title"><header><span className="eyebrow">WORKFLOW</span><h2 id="phase-progress-title">단계별 실행 경로</h2><p>단계 카드는 다음 업무 판단을 위한 진입점이며, 저장된 근거는 아래 증거 레일에서 확인합니다.</p></header><ol>{phaseActions.map((item, index) => { const phaseComplete = evidence.filter((entry) => entry.phase === item.phase.split(" ")[0]).every((entry) => entry.reference !== null); return <li key={item.phase} className={phaseComplete ? "is-complete" : ""}><span>{phaseComplete ? <CheckCircle2 aria-label="완료" /> : index + 1}</span><div><strong>{item.phase}</strong><p>{item.description}</p><Link className="text-link" to={item.to}>작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></li>; })}</ol></section>

      <section className="dmaic-evidence-panel" aria-labelledby="evidence-title"><header><div><span className="eyebrow">IMMUTABLE EVIDENCE RAIL</span><h2 id="evidence-title">프로젝트 증거 타임라인</h2><p>문서 ID·개정·해시는 저장된 API 계약을 그대로 표시합니다.</p></div>{nextEvidence && <Link className="button button-primary" to={nextEvidence.to}>다음 작업: {nextEvidence.label} <ArrowRight aria-hidden="true" /></Link>}</header><div className="dmaic-evidence-table" role="table" aria-label="DMAIC 프로젝트 증거"><div className="dmaic-evidence-row is-header" role="row"><span role="columnheader">단계</span><span role="columnheader">산출물</span><span role="columnheader">상태</span><span role="columnheader">문서 ID / 개정</span><span role="columnheader">무결성 해시</span><span role="columnheader">작업</span></div>{evidence.map((item) => <div className={`dmaic-evidence-row ${item.reference ? "is-recorded" : "is-pending"}`} role="row" key={item.key}><span role="cell" data-label="단계">{item.phase}</span><strong role="cell" data-label="산출물">{item.label}</strong><span role="cell" data-label="상태" className="evidence-status">{item.reference ? <><FileCheck2 aria-hidden="true" /> 저장됨</> : <><CircleDashed aria-hidden="true" /> 미작성</>}</span><code role="cell" data-label="문서 ID / 개정">{item.reference ? `${item.reference.document_id} / r${item.reference.revision}` : "—"}</code><code role="cell" data-label="무결성 해시">{item.reference ? `${item.reference.digest.slice(0, 12)}…` : "—"}</code><Link role="cell" className="text-link" to={item.to}>{item.reference ? "검토·개정" : "작성"} <ArrowRight aria-hidden="true" /></Link></div>)}</div></section>

      <section className="dmaic-project-integrations" aria-label="전문 분석 연결"><ShieldCheck aria-hidden="true" /><div><h2>전문 분석 근거 연결</h2><p>측정·원인·파일럿·관리 문서에서 DOE·SPC 분석 실행과 FMEA 관리항목을 선택하면 문서 개정에 불변 참조로 결합됩니다.</p><div><Link className="text-link" to="/doe">DOE 작업공간 <ArrowRight aria-hidden="true" /></Link><Link className="text-link" to="/spc">SPC 작업공간 <ArrowRight aria-hidden="true" /></Link><Link className="text-link" to="/fmea">FMEA 작업공간 <ArrowRight aria-hidden="true" /></Link></div></div></section>
    </>}
  </div>;
}

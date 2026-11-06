import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, ClipboardCheck, GitBranch, Layers3 } from "lucide-react";
import { Link } from "react-router-dom";
import { listDmaicProjects, saveDmaicSipoc } from "../api";
import { persistActiveProject, selectActiveProject } from "../projectContext";
import type { StoredDmaicProject } from "../types";

type SipocForm = {
  processStartBoundary: string; processEndBoundary: string; suppliers: string; inputs: string;
  processSteps: string; outputs: string; customers: string; actor: string;
};

const initialSipoc: SipocForm = {
  processStartBoundary: "", processEndBoundary: "", suppliers: "", inputs: "", processSteps: "",
  outputs: "", customers: "", actor: "local-operator",
};

const sipocFields: Array<{ key: Exclude<keyof SipocForm, "processStartBoundary" | "processEndBoundary" | "actor">; label: string; help: string }> = [
  { key: "suppliers", label: "공급자 (Suppliers)", help: "자재·정보·설비를 제공하는 부서 또는 협력사" },
  { key: "inputs", label: "입력 (Inputs)", help: "공정에 들어오는 자재·문서·조건" },
  { key: "processSteps", label: "공정 (Process)", help: "순서대로 실행되는 핵심 공정 단계" },
  { key: "outputs", label: "출력 (Outputs)", help: "공정에서 만들어지는 제품·정보·서비스" },
  { key: "customers", label: "고객 (Customers)", help: "출력을 사용하는 다음 공정·내부 또는 외부 고객" },
];

function asLines(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

export function DmaicSipocWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [sipoc, setSipoc] = useState<SipocForm>(initialSipoc);
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

  function update<K extends keyof SipocForm>(key: K, value: SipocForm[K]) {
    setSipoc((current) => ({ ...current, [key]: value }));
  }

  async function saveSipoc(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    try {
      const stored = await saveDmaicSipoc(selected.project_id, {
        expected_storage_version: selected.storage_version,
        process_start_boundary: sipoc.processStartBoundary, process_end_boundary: sipoc.processEndBoundary,
        suppliers: asLines(sipoc.suppliers), inputs: asLines(sipoc.inputs), process_steps: asLines(sipoc.processSteps),
        outputs: asLines(sipoc.outputs), customers: asLines(sipoc.customers), actor: sipoc.actor,
        occurred_at: new Date().toISOString(),
      });
      setProjects((current) => current.map((item) => item.project_id === stored.project_id ? stored : item));
      setSelected(stored); setSaved(stored); setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "SIPOC 공정 맵을 저장하지 못했습니다.");
    }
  }

  return <div className="page dmaic-sipoc-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic/define">정의 (Define)</Link><span aria-hidden="true">/</span><span>SIPOC 공정 맵 (SIPOC)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><GitBranch aria-hidden="true" /></span><div><span className="eyebrow">DEFINE · SIPOC · PROCESS MAP</span><h1>SIPOC 공정 맵 (SIPOC) 작업공간</h1><p>공급자부터 고객까지의 공정 경계와 핵심 흐름을 합의해, 측정·분석·개선의 범위와 책임을 명확하게 합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="SIPOC 공정 맵 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>경계</strong><p>시작·종료점 합의</p></div></li><li><span>3</span><div><strong>공정</strong><p>S-I-P-O-C 항목 기록</p></div></li><li><span>4</span><div><strong>검토</strong><p>측정 범위·책임 확인</p></div></li><li><span>5</span><div><strong>보고서</strong><p>불변 개정 저장</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>SIPOC 공정 맵은 선택한 프로젝트의 새 개정으로 보존됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { const project = projects.find((item) => item.project_id === event.target.value) ?? null; setSelected(project); persistActiveProject(project); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project.title} ({project.project_id})</option>)}</select></label><Link className="button button-secondary" to="/home/dmaic/define">프로젝트 헌장 열기</Link></div></section>
      {selected ? <form className="tool-workspace-panel dmaic-sipoc-form" onSubmit={saveSipoc}><header><h2>2. 공정 경계와 SIPOC 항목 작성</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision} · 각 항목은 한 줄에 하나씩 입력합니다.</p></header><div className="check-sheet-form"><label>공정 시작 경계<input value={sipoc.processStartBoundary} onChange={(event) => update("processStartBoundary", event.target.value)} placeholder="예: 입고 검사 완료" required /></label><label>공정 종료 경계<input value={sipoc.processEndBoundary} onChange={(event) => update("processEndBoundary", event.target.value)} placeholder="예: 출하 검사 완료" required /></label>{sipocFields.map((field) => <label key={field.key}>{field.label}<textarea value={sipoc[field.key]} onChange={(event) => update(field.key, event.target.value)} placeholder={field.help} required /><small>{field.help}</small></label>)}<label>저장 담당자<input value={sipoc.actor} onChange={(event) => update("actor", event.target.value)} required /></label></div><button className="primary-button" type="submit">SIPOC 공정 맵 저장 <ArrowRight aria-hidden="true" /></button></form> : <section className="tool-workspace-panel"><p className="method-note">SIPOC 공정 맵을 시작하려면 먼저 정의 작업공간에서 개선 프로젝트를 만드세요.</p><Link className="text-link" to="/home/dmaic/define">정의 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><ClipboardCheck aria-hidden="true" /><div><h2>SIPOC 공정 맵을 새 개정으로 저장했습니다</h2><p>프로젝트 {saved.project_id} · 개정 {saved.project.revision} · 측정 계획과 FMEA의 공정 범위 근거로 참조할 수 있습니다.</p></div></section>}
      <section className="tool-next-actions" aria-label="다음 작업"><article><Layers3 aria-hidden="true" /><div><h2>측정 계획으로 연결</h2><p>SIPOC에서 합의한 공정 경계와 출력 특성을 수집·표본·측정시스템 계획으로 전환합니다.</p><Link className="text-link" to="/home/dmaic/measure">측정 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ClipboardCheck aria-hidden="true" /><div><h2>SPC 기준선 확인</h2><p>공정 출력의 안정성과 특별원인 신호를 관리도로 확인합니다.</p><Link className="text-link" to="/spc">SPC 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

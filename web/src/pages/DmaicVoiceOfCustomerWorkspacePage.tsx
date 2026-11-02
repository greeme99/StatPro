import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, ClipboardCheck, MessageSquareText, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";
import { listDmaicProjects, saveDmaicVoiceOfCustomer } from "../api";
import type { StoredDmaicProject } from "../types";

type VocForm = {
  collectionPlan: string; dataPoints: string; requirements: string; painPoints: string;
  opportunities: string; actions: string; recommendations: string; nextSteps: string; actor: string;
};

const initialVoc: VocForm = {
  collectionPlan: "", dataPoints: "", requirements: "", painPoints: "", opportunities: "",
  actions: "", recommendations: "", nextSteps: "", actor: "local-operator",
};

function asLines(value: string): string[] {
  return value.split("\n").map((item) => item.trim()).filter(Boolean);
}

const fields: Array<{ key: Exclude<keyof VocForm, "collectionPlan" | "actor">; label: string }> = [
  { key: "dataPoints", label: "고객 데이터·관찰" }, { key: "requirements", label: "고객 요구사항" },
  { key: "painPoints", label: "불편·문제점" }, { key: "opportunities", label: "개선 기회" },
  { key: "actions", label: "우선 조치" }, { key: "recommendations", label: "권고사항" },
  { key: "nextSteps", label: "다음 단계" },
];

export function DmaicVoiceOfCustomerWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [voc, setVoc] = useState<VocForm>(initialVoc);
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

  function update<K extends keyof VocForm>(key: K, value: VocForm[K]) {
    setVoc((current) => ({ ...current, [key]: value }));
  }

  async function saveVoc(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    try {
      const stored = await saveDmaicVoiceOfCustomer(selected.project_id, {
        expected_storage_version: selected.storage_version,
        collection_plan: voc.collectionPlan,
        data_points: asLines(voc.dataPoints), requirements: asLines(voc.requirements),
        pain_points: asLines(voc.painPoints), opportunities: asLines(voc.opportunities),
        actions: asLines(voc.actions), recommendations: asLines(voc.recommendations),
        next_steps: asLines(voc.nextSteps), actor: voc.actor, occurred_at: new Date().toISOString(),
      });
      setProjects((current) => current.map((item) => item.project_id === stored.project_id ? stored : item));
      setSelected(stored); setSaved(stored); setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "고객의 소리 자료를 저장하지 못했습니다.");
    }
  }

  return <div className="page dmaic-voc-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span aria-hidden="true">/</span><Link to="/home/dmaic/define">정의 (Define)</Link><span aria-hidden="true">/</span><span>고객의 소리 (VOC)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><MessageSquareText aria-hidden="true" /></span><div><span className="eyebrow">DEFINE · VOC · REQUIREMENTS</span><h1>고객의 소리 (VOC) 작업공간</h1><p>고객 요구사항과 현장 관찰을 실행 가능한 개선 과제로 구조화하고, 프로젝트 개정 이력으로 보존합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="고객의 소리 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>개선 프로젝트 선택</p></div></li><li><span>2</span><div><strong>데이터</strong><p>고객 관찰·요구 기록</p></div></li><li><span>3</span><div><strong>분석</strong><p>불편과 기회 정리</p></div></li><li><span>4</span><div><strong>결과</strong><p>조치·권고 합의</p></div></li><li><span>5</span><div><strong>보고서</strong><p>불변 개정 저장</p></div></li></ol>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <>
      <section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>VOC 기록은 선택한 프로젝트의 새 개정으로 보존됩니다.</p></header><div className="dmaic-project-picker"><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { setSelected(projects.find((project) => project.project_id === event.target.value) ?? null); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project.title} ({project.project_id})</option>)}</select></label><Link className="button button-secondary" to="/home/dmaic/define">프로젝트 헌장 열기</Link></div></section>
      {selected ? <form className="tool-workspace-panel dmaic-voc-form" onSubmit={saveVoc}><header><h2>2. 고객 요구사항과 조치 정리</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label className="check-sheet-wide">수집 계획<textarea value={voc.collectionPlan} onChange={(event) => update("collectionPlan", event.target.value)} placeholder="대상 고객, 수집 채널, 기간, 책임자를 적으세요." required /></label>{fields.map((field) => <label key={field.key}>{field.label}<textarea value={voc[field.key]} onChange={(event) => update(field.key, event.target.value)} placeholder="한 줄에 하나씩 입력" required /></label>)}<label>저장 담당자<input value={voc.actor} onChange={(event) => update("actor", event.target.value)} required /></label></div><button className="primary-button" type="submit">VOC 기록 저장 <ArrowRight aria-hidden="true" /></button></form> : <section className="tool-workspace-panel"><p className="method-note">VOC 기록을 시작하려면 먼저 정의 작업공간에서 개선 프로젝트를 만드세요.</p><Link className="text-link" to="/home/dmaic/define">정의 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><ClipboardCheck aria-hidden="true" /><div><h2>고객의 소리 기록을 새 개정으로 저장했습니다</h2><p>프로젝트 {saved.project_id} · 개정 {saved.project.revision} · 측정 계획과 개선 실험에서 요구사항 근거로 참조할 수 있습니다.</p></div></section>}
      <section className="tool-next-actions" aria-label="다음 작업"><article><UsersRound aria-hidden="true" /><div><h2>측정 계획으로 연결</h2><p>요구사항을 측정 가능한 지표와 수집·표본 계획으로 전환합니다.</p><Link className="text-link" to="/home/dmaic/measure">측정 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><ClipboardCheck aria-hidden="true" /><div><h2>SPC로 기준선 확인</h2><p>품질 특성을 관리도로 관찰해 개선 전 공정 상태를 확인합니다.</p><Link className="text-link" to="/spc">SPC 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

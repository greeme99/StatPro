import { ArrowLeft, Fish, Plus, ShieldCheck } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { addFishboneCause, createFishbone } from "../api";
import { FishboneDiagram } from "../components/FishboneDiagram";
import type { StoredFishbone } from "../types";

const categories = [
  { category_id: "man", name: "사람(Man)" },
  { category_id: "machine", name: "설비(Machine)" },
  { category_id: "material", name: "재료(Material)" },
  { category_id: "method", name: "방법(Method)" },
  { category_id: "measurement", name: "측정(Measurement)" },
  { category_id: "environment", name: "환경(Environment)" },
];

export function FishboneWorkspacePage() {
  const [stored, setStored] = useState<StoredFishbone | null>(null);
  const [diagramId, setDiagramId] = useState(`fishbone-${Date.now()}`);
  const [title, setTitle] = useState("조립 스크래치 원인 분석");
  const [processName, setProcessName] = useState("조립 1라인");
  const [problem, setProblem] = useState("외관 스크래치가 목표를 초과한다.");
  const [categoryId, setCategoryId] = useState("man");
  const [causeText, setCauseText] = useState("");
  const [evidence, setEvidence] = useState("");
  const [selected, setSelected] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const causeCount = useMemo(() => stored?.diagram.categories.reduce((sum, category) => sum + category.causes.length, 0) ?? 0, [stored]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError("");
    try {
      setStored(await createFishbone({ diagram_id: diagramId, title, process_name: processName, problem_statement: problem, categories }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "특성요인도를 만들지 못했습니다.");
    } finally { setBusy(false); }
  }

  async function addCause(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    setBusy(true); setError("");
    try {
      const causeId = `cause-${Date.now()}`;
      const updated = await addFishboneCause(stored.diagram_id, {
        expected_storage_version: stored.storage_version,
        category_id: categoryId,
        cause_id: causeId,
        text: causeText,
        evidence_refs: evidence.split(",").map((item) => item.trim()).filter(Boolean),
        selected_for_verification: selected,
      });
      setStored(updated); setCauseText(""); setEvidence(""); setSelected(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "원인 후보를 추가하지 못했습니다.");
    } finally { setBusy(false); }
  }

  return <div className="page fishbone-workspace" data-density="comfortable">
    <Link className="back-link" to="/spc"><ArrowLeft aria-hidden="true" /> SPC 작업공간</Link>
    <section className="spc-tool-hero"><span className="preview-icon"><Fish aria-hidden="true" /></span><div><span className="eyebrow">STRUCTURE · VERIFY · TRACE</span><h1>특성요인도(Fishbone Diagram) 작업공간</h1><p>팀의 원인 가설을 6M 범주로 구조화하고, 검증할 후보와 근거 참조를 개정 이력과 함께 보존합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="특성요인도 업무 단계">
      <li><span>1</span><div><strong>문제 정의</strong><p>현상과 공정 경계를 명확히 합니다.</p></div></li>
      <li><span>2</span><div><strong>범주 전개</strong><p>6M 기준으로 원인을 발산합니다.</p></div></li>
      <li><span>3</span><div><strong>증거 연결</strong><p>관찰·분석 참조를 남깁니다.</p></div></li>
      <li><span>4</span><div><strong>검증 선정</strong><p>시험할 가설을 표시합니다.</p></div></li>
      <li><span>5</span><div><strong>후속 분석</strong><p>DOE·SPC 조치로 연결합니다.</p></div></li>
    </ol>
    {!stored ? <form className="tool-workspace-panel fishbone-form" onSubmit={create}>
      <header><h2>1. 분석 범위 설정</h2><p>특성요인도는 브레인스토밍 구조이며 인과관계의 통계적 증명이 아닙니다.</p></header>
      <label>문서 ID<input value={diagramId} onChange={(event) => setDiagramId(event.target.value)} pattern="[A-Za-z0-9][A-Za-z0-9._-]*" required /></label>
      <label>분석 제목<input value={title} onChange={(event) => setTitle(event.target.value)} required /></label>
      <label>대상 공정<input value={processName} onChange={(event) => setProcessName(event.target.value)} required /></label>
      <label className="fishbone-wide">문제 진술<textarea value={problem} onChange={(event) => setProblem(event.target.value)} required /></label>
      <button className="primary-button fishbone-wide" type="submit" disabled={busy}>{busy ? "작업공간 생성 중…" : "6M 작업공간 만들기"}</button>
    </form> : <>
      <section className="fishbone-status" aria-label="특성요인도 상태"><div><span>개정</span><strong>{stored.diagram.revision}</strong></div><div><span>원인 후보</span><strong>{causeCount}</strong></div><div><span>검증 대상</span><strong>{stored.diagram.categories.flatMap((item) => item.causes).filter((item) => item.selected_for_verification).length}</strong></div><div><span>저장 버전</span><strong>{stored.storage_version}</strong></div></section>
      <section className="tool-workspace-panel"><header><h2>2. 원인 구조와 검증 대상</h2><p>{stored.diagram.process_name} · 스냅샷 {stored.diagram.digest.slice(0, 12)}</p></header><FishboneDiagram diagram={stored.diagram} /></section>
      <form className="tool-workspace-panel fishbone-cause-form" onSubmit={addCause}>
        <header><h2>3. 원인 후보 추가</h2><p>객관적 확인 자료가 있으면 분석 실행 ID, 사진, 검사 기록 등의 참조를 함께 입력합니다.</p></header>
        <label>6M 범주<select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>{categories.map((category) => <option key={category.category_id} value={category.category_id}>{category.name}</option>)}</select></label>
        <label>원인 후보<input value={causeText} onChange={(event) => setCauseText(event.target.value)} required /></label>
        <label className="fishbone-wide">증거 참조(쉼표로 구분)<input value={evidence} onChange={(event) => setEvidence(event.target.value)} placeholder="run:pareto-01, photo:guide-02" /></label>
        <label className="checkbox-field"><input type="checkbox" checked={selected} onChange={(event) => setSelected(event.target.checked)} /><ShieldCheck aria-hidden="true" /> 검증 과제로 선정</label>
        <button className="primary-button" type="submit" disabled={busy || !causeText.trim()}><Plus aria-hidden="true" /> {busy ? "추가 중…" : "원인 후보 추가"}</button>
      </form>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

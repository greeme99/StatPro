import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AlertTriangle, ArrowRight, Bug, FileCheck2, Plus, RotateCcw, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { createDefectAnalysis, listDefectAnalyses, reviseDefectAnalysis } from "../api";
import type { DefectCategory, StoredDefectAnalysis } from "../types";

type FormState = {
  analysisId: string; title: string; processName: string; period: string;
  ownerRef: string; sourceCheckSheetId: string; categories: DefectCategory[];
};

const emptyCategory = (): DefectCategory => ({ category: "", defect_count: 0, opportunity_count: 1, unit_loss: 0, severity: 1 });
const initialForm = (): FormState => ({ analysisId: "", title: "", processName: "", period: "", ownerRef: "quality.team", sourceCheckSheetId: "", categories: [emptyCategory()] });

export function DefectAnalysisPage() {
  const [items, setItems] = useState<StoredDefectAnalysis[]>([]);
  const [selected, setSelected] = useState<StoredDefectAnalysis | null>(null);
  const [revisionBase, setRevisionBase] = useState<StoredDefectAnalysis | null>(null);
  const [form, setForm] = useState<FormState>(initialForm);
  const [state, setState] = useState<"loading" | "ready" | "saving" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    listDefectAnalyses(100).then((page) => { setItems(page.items); setSelected(page.items[0] ?? null); setState("ready"); })
      .catch((error: Error) => { setMessage(error.message); setState("error"); });
  }, []);

  const latest = selected ?? items[0] ?? null;
  const overview = useMemo(() => latest?.summary ?? null, [latest]);
  const updateCategory = (index: number, field: keyof DefectCategory, value: string) => {
    setForm((current) => ({ ...current, categories: current.categories.map((row, rowIndex) => rowIndex === index ? { ...row, [field]: field === "category" ? value : Number(value) } : row) }));
  };
  const beginRevision = (stored: StoredDefectAnalysis) => {
    setSelected(stored);
    setRevisionBase(stored);
    setForm({ analysisId: stored.analysis_id, title: stored.analysis.title, processName: stored.analysis.process_name, period: stored.analysis.period, ownerRef: stored.analysis.owner_ref, sourceCheckSheetId: stored.analysis.source?.check_sheet_id ?? "", categories: stored.analysis.categories.map((row) => ({ ...row })) });
    setMessage("선택한 문서의 새 개정을 작성합니다. 기존 개정은 변경되지 않습니다.");
  };
  const reset = () => { setForm(initialForm()); setRevisionBase(null); setMessage(""); };
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setState("saving"); setMessage("");
    const payload = { title: form.title, process_name: form.processName, period: form.period, owner_ref: form.ownerRef, source_check_sheet_id: form.sourceCheckSheetId || null, categories: form.categories };
    try {
      const saved = revisionBase
        ? await reviseDefectAnalysis(revisionBase.analysis_id, { ...payload, expected_storage_version: revisionBase.storage_version })
        : await createDefectAnalysis({ ...payload, analysis_id: form.analysisId });
      setItems((current) => [saved, ...current.filter((item) => item.analysis_id !== saved.analysis_id)]);
      setSelected(saved); setRevisionBase(saved); setState("ready"); setMessage(`결함 분석 개정 ${saved.analysis.revision}을 저장했습니다.`);
    } catch (error) { setState("error"); setMessage(error instanceof Error ? error.message : "결함 분석을 저장하지 못했습니다."); }
  };

  return <div className="page defect-workspace">
    <nav className="breadcrumbs" aria-label="현재 위치"><Link to="/home">홈 (Home)</Link><span>/</span><span>결함 분석 (Defect Analysis)</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><Bug aria-hidden="true" /></span><div><span className="eyebrow">COUNT · OPPORTUNITY · LOSS · RISK</span><h1>결함 분석 (Defect Analysis) 작업공간</h1><p>체크 시트 발생 건수와 검사 기회, 단위 손실, 심각도를 결합해 개선 우선순위를 개정 이력으로 보존합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="결함 분석 작업 흐름"><li><span>1</span><div><strong>설정</strong><p>공정·기간 정의</p></div></li><li><span>2</span><div><strong>데이터</strong><p>결함·기회 입력</p></div></li><li><span>3</span><div><strong>분석</strong><p>DPMO·손실·위험</p></div></li><li><span>4</span><div><strong>결과</strong><p>우선순위 검토</p></div></li><li><span>5</span><div><strong>보고서</strong><p>개정·근거 보존</p></div></li></ol>
    {message && <div className={state === "error" ? "error-banner" : "quality-confirmation"} role={state === "error" ? "alert" : "status"}>{state === "error" ? <AlertTriangle /> : <FileCheck2 />}<p>{message}</p></div>}
    {overview && <section className="quality-summary-grid" aria-label="최근 분석 요약"><article><Bug /><span>총 결함</span><strong>{overview.total_defects.toLocaleString("ko-KR")}</strong></article><article><FileCheck2 /><span>DPMO</span><strong>{overview.dpmo.toLocaleString("ko-KR", { maximumFractionDigits: 1 })}</strong></article><article><AlertTriangle /><span>추정 손실</span><strong>{overview.estimated_loss.toLocaleString("ko-KR")}</strong></article><article><ArrowRight /><span>최우선 범주</span><strong>{overview.top_risk_category}</strong></article></section>}
    <div className="defect-layout">
      <section className="tool-workspace-panel"><header><h2>저장된 결함 분석</h2><p>각 문서는 불변 개정과 이전 개정 다이제스트를 보존합니다.</p></header>{items.length === 0 ? <p className="method-note">저장된 분석이 없습니다.</p> : <div className="defect-document-list">{items.map((item) => <button type="button" key={item.analysis_id} className={selected?.analysis_id === item.analysis_id ? "is-selected" : ""} onClick={() => setSelected(item)}><span><strong>{item.analysis.title}</strong><small>{item.analysis.process_name} · {item.analysis.period}</small></span><span>개정 {item.analysis.revision}</span></button>)}</div>}{selected && <><div className="table-wrap"><table><thead><tr><th>범주</th><th>결함</th><th>DPMO</th><th>손실</th><th>위험점수</th></tr></thead><tbody>{selected.summary.categories.map((row) => <tr key={row.category}><td>{row.category}</td><td>{row.defect_count}</td><td>{row.dpmo.toLocaleString("ko-KR", { maximumFractionDigits: 1 })}</td><td>{row.estimated_loss.toLocaleString("ko-KR")}</td><td>{row.risk_score}</td></tr>)}</tbody></table></div><details><summary>추적 근거</summary><p className="digest">문서: {selected.analysis.digest}</p><p className="digest">이전 개정: {selected.analysis.parent_digest ?? "없음"}</p><p className="digest">체크 시트: {selected.analysis.source?.check_sheet_id ?? "수동 입력"}</p></details><button type="button" className="secondary-button" onClick={() => beginRevision(selected)}>새 개정 작성</button></>}</section>
      <form className="tool-workspace-panel defect-form" onSubmit={submit}><header><h2>{revisionBase ? "결함 분석 개정" : "새 결함 분석"}</h2><button type="button" className="icon-button" aria-label="새 문서로 초기화" onClick={reset}><RotateCcw /></button></header><div className="check-sheet-form"><label>분석 ID<input value={form.analysisId} disabled={Boolean(revisionBase)} required onChange={(event) => setForm({ ...form, analysisId: event.target.value })} /></label><label>분석명<input value={form.title} required onChange={(event) => setForm({ ...form, title: event.target.value })} /></label><label>공정명<input value={form.processName} required onChange={(event) => setForm({ ...form, processName: event.target.value })} /></label><label>분석 기간<input value={form.period} required placeholder="예: 2026-W45" onChange={(event) => setForm({ ...form, period: event.target.value })} /></label><label>담당자<input value={form.ownerRef} required onChange={(event) => setForm({ ...form, ownerRef: event.target.value })} /></label><label>체크 시트 ID (선택)<input value={form.sourceCheckSheetId} onChange={(event) => setForm({ ...form, sourceCheckSheetId: event.target.value })} /></label></div>
        <div className="defect-category-heading"><div><h3>결함 범주</h3><p>체크 시트를 연결하면 범주별 결함 수가 저장된 집계와 정확히 일치해야 합니다.</p></div><button type="button" className="secondary-button" onClick={() => setForm((current) => ({ ...current, categories: [...current.categories, emptyCategory()] }))}><Plus /> 범주 추가</button></div>
        <div className="defect-category-table"><div className="defect-category-row is-heading"><span>범주</span><span>결함 수</span><span>검사 기회</span><span>단위 손실</span><span>심각도</span><span /></div>{form.categories.map((row, index) => <div className="defect-category-row" key={index}><input aria-label={`범주 ${index + 1}`} required value={row.category} onChange={(event) => updateCategory(index, "category", event.target.value)} /><input aria-label={`결함 수 ${index + 1}`} type="number" min="0" required value={row.defect_count} onChange={(event) => updateCategory(index, "defect_count", event.target.value)} /><input aria-label={`검사 기회 ${index + 1}`} type="number" min="1" required value={row.opportunity_count} onChange={(event) => updateCategory(index, "opportunity_count", event.target.value)} /><input aria-label={`단위 손실 ${index + 1}`} type="number" min="0" step="any" value={row.unit_loss} onChange={(event) => updateCategory(index, "unit_loss", event.target.value)} /><input aria-label={`심각도 ${index + 1}`} type="number" min="1" max="10" value={row.severity} onChange={(event) => updateCategory(index, "severity", event.target.value)} /><button type="button" className="icon-button" aria-label={`범주 ${index + 1} 삭제`} disabled={form.categories.length === 1} onClick={() => setForm((current) => ({ ...current, categories: current.categories.filter((_, rowIndex) => rowIndex !== index) }))}><Trash2 /></button></div>)}</div>
        <p className="method-note">DPMO는 입력한 검사 기회 기준의 우선순위 지표이며 시그마 수준을 자동 주장하지 않습니다. 추정 손실은 회계 확정값이 아닙니다.</p><button className="primary-button" type="submit" disabled={state === "saving"}>{state === "saving" ? "저장 중…" : revisionBase ? "새 개정 저장" : "결함 분석 저장"}</button>
      </form>
    </div>
  </div>;
}

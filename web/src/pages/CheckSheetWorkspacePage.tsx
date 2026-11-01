import { FormEvent, useState } from "react";
import { ArrowLeft, ArrowRight, ClipboardCheck, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import { addCheckSheetRecord, createCheckSheet } from "../api";
import type { StoredCheckSheet } from "../types";

export function CheckSheetWorkspacePage() {
  const [stored, setStored] = useState<StoredCheckSheet | null>(null);
  const [error, setError] = useState("");

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    try {
      setStored(await createCheckSheet({
        sheet_id: String(data.get("sheet_id")), title: String(data.get("title")),
        process_name: String(data.get("process_name")), category_label: String(data.get("category_label")),
      }));
      setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "체크 시트를 만들지 못했습니다."); }
  }

  async function addRecord(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    try {
      setStored(await addCheckSheetRecord(stored.sheet_id, {
        expected_storage_version: stored.storage_version,
        record_id: `record-${Date.now()}`,
        category: String(data.get("category")), count: Number(data.get("count")),
        observed_at: String(data.get("observed_at")) || null,
        location: String(data.get("location")) || null,
        shift: String(data.get("shift")) || null,
        lot: String(data.get("lot")) || null,
        note: String(data.get("note")) || null,
      }));
      form.reset();
      setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "기록을 추가하지 못했습니다."); }
  }

  const frequencies = (stored?.summary.tables.frequencies ?? []) as Array<{ category: string; count: number; percentage: number }>;
  const total = Number(stored?.summary.tables.summary?.total ?? 0);

  return <div className="page check-sheet-workspace" data-density="comfortable">
    <Link className="back-link" to="/spc"><ArrowLeft aria-hidden="true" /> SPC 작업공간</Link>
    <section className="spc-tool-hero"><span className="preview-icon"><ClipboardCheck aria-hidden="true" /></span><div><span className="eyebrow">COLLECT · TALLY · PRIORITIZE</span><h1>체크 시트(Check Sheet) 작업공간</h1><p>현장 발생 사실을 동일한 분류 기준으로 기록하고 빈도를 집계해 파레토 분석과 관리도로 연결합니다.</p></div></section>
    {!stored ? <section className="tool-workspace-panel"><header><h2>1. 수집 기준 정의</h2><p>공정과 분류 항목을 먼저 고정해 기록자의 해석 차이를 줄입니다.</p></header><form className="check-sheet-form" onSubmit={create}>
      <label>체크 시트 ID<input name="sheet_id" defaultValue="assembly-defects" required /></label>
      <label>제목<input name="title" defaultValue="조립 외관 불량" required /></label>
      <label>공정명<input name="process_name" defaultValue="조립 1라인" required /></label>
      <label>분류 항목명<input name="category_label" defaultValue="불량 유형" required /></label>
      <button className="primary-button" type="submit">체크 시트 만들기 <ArrowRight aria-hidden="true" /></button>
    </form></section> : <>
      <section className="check-sheet-status" aria-label="체크 시트 상태"><div><span>공정</span><strong>{stored.sheet.process_name}</strong></div><div><span>개정</span><strong>{stored.sheet.revision}</strong></div><div><span>총 발생</span><strong>{total}</strong></div><div><span>분류 수</span><strong>{frequencies.length}</strong></div></section>
      <section className="check-sheet-grid"><form className="tool-workspace-panel check-sheet-form" onSubmit={addRecord}><header><h2>2. 현장 기록 추가</h2><p>{stored.sheet.category_label}, 시간, 위치, 교대조와 로트를 함께 남깁니다.</p></header>
        <label>{stored.sheet.category_label}<input name="category" required /></label><label>발생 수<input name="count" type="number" min="1" defaultValue="1" required /></label><label>관찰 시각<input name="observed_at" type="datetime-local" /></label><label>위치<input name="location" /></label><label>교대조<input name="shift" /></label><label>로트<input name="lot" /></label><label className="check-sheet-wide">메모<input name="note" /></label><button className="primary-button check-sheet-wide" type="submit"><Plus aria-hidden="true" /> 기록 추가</button>
      </form><section className="tool-workspace-panel"><header><h2>3. 빈도 집계</h2><p>발생 수 기준 내림차순으로 우선순위를 확인합니다.</p></header>{frequencies.length === 0 ? <p className="method-note">첫 기록을 추가하면 집계 결과가 표시됩니다.</p> : <div className="table-wrap"><table><thead><tr><th>분류</th><th>발생 수</th><th>비율</th></tr></thead><tbody>{frequencies.map(row => <tr key={row.category}><td>{row.category}</td><td>{row.count}</td><td>{row.percentage.toFixed(1)}%</td></tr>)}</tbody></table></div>}<Link className="text-link" to="/spc/tools/pareto-chart">파레토 차트로 후속 분석 <ArrowRight aria-hidden="true" /></Link></section></section>
      <section className="tool-workspace-panel"><header><h2>수집 기록</h2><p>현재 개정에 포함된 원시 기록이며, 집계 결과의 추적 근거입니다.</p></header><div className="table-wrap"><table><thead><tr><th>{stored.sheet.category_label}</th><th>발생 수</th><th>관찰 시각</th><th>위치</th><th>교대조</th><th>로트</th></tr></thead><tbody>{stored.sheet.records.map(record => <tr key={record.record_id}><td>{record.category}</td><td>{record.count}</td><td>{record.observed_at || "-"}</td><td>{record.location || "-"}</td><td>{record.shift || "-"}</td><td>{record.lot || "-"}</td></tr>)}</tbody></table></div></section>
    </>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}

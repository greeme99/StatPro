import { AlertTriangle, ArrowLeft, Database, Pencil, Save } from "lucide-react";
import { type FormEvent, type MouseEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getWorksheet, replaceWorksheetCell } from "../api";
import { Button } from "../components/Button";
import type { DataColumn, StoredWorksheet } from "../types";

type SelectedCell = { rowIndex: number; column: DataColumn };

export function WorksheetPage() {
  const { worksheetId = "" } = useParams();
  const editorRef = useRef<HTMLInputElement>(null);
  const drawerRef = useRef<HTMLElement>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [stored, setStored] = useState<StoredWorksheet | null>(null);
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null);
  const [selectedCell, setSelectedCell] = useState<SelectedCell | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    getWorksheet(worksheetId)
      .then((value) => { if (active) { setStored(value); setSelectedColumn(value.worksheet.columns[0]?.name ?? null); } })
      .catch((requestError) => { if (active) setError(requestError instanceof Error ? requestError.message : "워크시트를 불러오지 못했습니다."); });
    return () => { active = false; };
  }, [worksheetId]);

  useEffect(() => {
    if (!selectedCell) return;
    editorRef.current?.focus();
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") { event.preventDefault(); closeEditor(); return; }
      if (event.key !== "Tab" || !drawerRef.current) return;
      const focusable = [...drawerRef.current.querySelectorAll<HTMLElement>("button, input, select, textarea, a[href]")].filter((element) => !element.hasAttribute("disabled"));
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [selectedCell]);
  const profile = useMemo(() => stored?.worksheet.columns.find((column) => column.name === selectedColumn) ?? null, [stored, selectedColumn]);
  const numericRange = useMemo(() => {
    if (!profile || profile.data_type !== "numeric") return null;
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    for (const value of profile.values) {
      if (typeof value === "number") { min = Math.min(min, value); max = Math.max(max, value); }
    }
    return Number.isFinite(min) ? { min, max } : null;
  }, [profile]);

  function openEditor(event: MouseEvent<HTMLButtonElement>, cell: SelectedCell) {
    triggerRef.current = event.currentTarget;
    setSelectedCell(cell);
  }

  function closeEditor() {
    setSelectedCell(null);
    requestAnimationFrame(() => triggerRef.current?.focus());
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored || !selectedCell) return;
    const form = new FormData(event.currentTarget);
    const raw = String(form.get("value") ?? "");
    setBusy(true);
    setError("");
    try {
      const revised = await replaceWorksheetCell(worksheetId, {
        expected_storage_version: stored.storage_version,
        row_index: selectedCell.rowIndex,
        column_name: selectedCell.column.name,
        value: raw === "" ? null : raw,
      });
      setStored(revised);
      closeEditor();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "셀을 저장하지 못했습니다.");
    } finally { setBusy(false); }
  }

  if (!stored) return <div className="page" data-density="compact">{error ? <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div> : <div className="skeleton page-skeleton" aria-label="워크시트 불러오는 중" />}</div>;
  const { worksheet } = stored;
  const visibleRows = Math.min(worksheet.row_count, 200);

  return <div className="page worksheet-page" data-density="compact">
    <Link className="back-link" to="/data"><ArrowLeft aria-hidden="true" /> 워크시트 목록</Link>
    <section className="result-header"><div><span className="eyebrow">WORKSHEET</span><h1>{worksheet.name}</h1><p>{worksheet.worksheet_id} · revision {worksheet.revision} · {worksheet.row_count}행 × {worksheet.columns.length}열</p></div><span className="status-badge status-approved">저장됨</span></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div>}
    <section className="worksheet-layout">
      <aside className="panel column-profile"><header className="panel-heading"><div><span className="eyebrow">COLUMN PROFILE</span><h2>{profile?.name ?? "열 선택"}</h2></div><Database aria-hidden="true" /></header>{profile && <dl><div><dt>타입</dt><dd>{profile.data_type}</dd></div><div><dt>결측</dt><dd>{profile.missing_count}</dd></div>{numericRange && <><div><dt>최솟값</dt><dd>{numericRange.min}</dd></div><div><dt>최댓값</dt><dd>{numericRange.max}</dd></div></>}</dl>}</aside>
      <article className="panel worksheet-grid-panel"><header className="panel-heading"><div><span className="eyebrow">DATA GRID</span><h2>데이터</h2></div><span>최대 200행 표시</span></header><div className="table-scroll worksheet-scroll"><table className="worksheet-table"><thead><tr><th scope="col">행</th>{worksheet.columns.map((column) => <th scope="col" key={column.name}><button type="button" onClick={() => setSelectedColumn(column.name)}>{column.name}<small>{column.data_type} · 결측 {column.missing_count}</small></button></th>)}</tr></thead><tbody>{Array.from({ length: visibleRows }, (_, rowIndex) => <tr key={rowIndex}><th scope="row">{rowIndex + 1}</th>{worksheet.columns.map((column) => { const value = column.values[rowIndex]; return <td key={column.name}><button type="button" className="cell-button" onClick={(event) => openEditor(event, { rowIndex, column })} aria-label={`행 ${rowIndex + 1}, 열 ${column.name}, 값 ${value === null ? "결측" : String(value)} 편집`}>{value === null ? <span className="missing-value">—<span className="sr-only">결측</span></span> : String(value)}</button></td>; })}</tr>)}</tbody></table></div>{worksheet.row_count > visibleRows && <p className="table-limit-note">성능 보호를 위해 처음 200행만 표시합니다. 원본에는 {worksheet.row_count}행이 보존됩니다.</p>}</article>
    </section>
    {selectedCell && <><button className="drawer-scrim" type="button" aria-label="셀 편집 닫기" onClick={closeEditor} /><aside ref={drawerRef} className="detail-drawer cell-editor" role="dialog" aria-modal="true" aria-labelledby="cell-editor-title"><header><div><span className="eyebrow">CELL EDIT</span><h2 id="cell-editor-title">{selectedCell.column.name} · 행 {selectedCell.rowIndex + 1}</h2></div><button className="icon-button" type="button" aria-label="닫기" onClick={closeEditor}>×</button></header><form onSubmit={handleSave}><label className="field">새 값<input ref={editorRef} name="value" defaultValue={selectedCell.column.values[selectedCell.rowIndex] === null ? "" : String(selectedCell.column.values[selectedCell.rowIndex])} /><small>빈 값으로 저장하면 결측값이 됩니다. 열 타입은 {selectedCell.column.data_type}입니다.</small></label><Button type="submit" variant="primary" loading={busy} icon={<Save />}>새 revision으로 저장</Button></form><p className="method-note"><Pencil aria-hidden="true" /> 현재 revision은 변경하지 않고 부모 digest가 연결된 새 revision을 생성합니다.</p></aside></>}
  </div>;
}

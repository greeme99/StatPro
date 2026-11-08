import { AlertTriangle, ArrowLeft, Database, Filter, ListFilter, Pencil, Save, Sigma } from "lucide-react";
import { type FormEvent, type MouseEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { addDerivedNumericColumn, filterWorksheetRows, getWorksheet, replaceWorksheetCell, sortWorksheetRows } from "../api";
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

  async function applyTransformation(work: () => Promise<StoredWorksheet>) {
    setBusy(true);
    setError("");
    try {
      const revised = await work();
      setStored(revised);
      setSelectedColumn(revised.worksheet.columns[0]?.name ?? null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "작업표 변환을 저장하지 못했습니다.");
    } finally { setBusy(false); }
  }

  function handleFilterRows(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const form = new FormData(event.currentTarget);
    const operator = String(form.get("operator") ?? "equals") as "equals" | "not_equals" | "greater_than" | "greater_or_equal" | "less_than" | "less_or_equal" | "contains" | "is_missing" | "is_not_missing";
    const rawValue = String(form.get("value") ?? "");
    void applyTransformation(() => filterWorksheetRows(worksheetId, {
      expected_storage_version: stored.storage_version,
      column_name: String(form.get("column_name") ?? ""),
      operator,
      value: operator === "is_missing" || operator === "is_not_missing" ? undefined : rawValue,
    }));
  }

  function handleSortRows(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const form = new FormData(event.currentTarget);
    void applyTransformation(() => sortWorksheetRows(worksheetId, {
      expected_storage_version: stored.storage_version,
      column_name: String(form.get("column_name") ?? ""),
      descending: form.get("descending") === "on",
    }));
  }

  function handleDerivedColumn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!stored) return;
    const form = new FormData(event.currentTarget);
    const operation = String(form.get("operation") ?? "copy") as "copy" | "add" | "subtract" | "multiply" | "divide";
    const operandMode = String(form.get("operand_mode") ?? "column");
    const rawConstant = String(form.get("operand_constant") ?? "").trim();
    void applyTransformation(() => addDerivedNumericColumn(worksheetId, {
      expected_storage_version: stored.storage_version,
      column_name: String(form.get("column_name") ?? "").trim(),
      source_column: String(form.get("source_column") ?? ""),
      operation,
      ...(operation === "copy" ? {} : operandMode === "column"
        ? { operand_column: String(form.get("operand_column") ?? "") }
        : { operand_constant: Number(rawConstant) }),
    }));
  }

  if (!stored) return <div className="page" data-density="compact">{error ? <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div> : <div className="skeleton page-skeleton" aria-label="워크시트 불러오는 중" />}</div>;
  const { worksheet } = stored;
  const visibleRows = Math.min(worksheet.row_count, 200);
  const numericColumns = worksheet.columns.filter((column) => column.data_type === "numeric");

  return <div className="page worksheet-page" data-density="compact">
    <Link className="back-link" to="/data"><ArrowLeft aria-hidden="true" /> 워크시트 목록</Link>
    <section className="result-header"><div><span className="eyebrow">WORKSHEET</span><h1>{worksheet.name}</h1><p>{worksheet.worksheet_id} · revision {worksheet.revision} · {worksheet.row_count}행 × {worksheet.columns.length}열</p></div><span className="status-badge status-approved">저장됨</span></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div>}
    <section className="worksheet-layout">
      <aside className="panel column-profile"><header className="panel-heading"><div><span className="eyebrow">COLUMN PROFILE</span><h2>{profile?.name ?? "열 선택"}</h2></div><Database aria-hidden="true" /></header>{profile && <dl><div><dt>타입</dt><dd>{profile.data_type}</dd></div><div><dt>결측</dt><dd>{profile.missing_count}</dd></div>{numericRange && <><div><dt>최솟값</dt><dd>{numericRange.min}</dd></div><div><dt>최댓값</dt><dd>{numericRange.max}</dd></div></>}</dl>}</aside>
      <article className="panel worksheet-grid-panel"><header className="panel-heading"><div><span className="eyebrow">DATA GRID</span><h2>데이터</h2></div><span>최대 200행 표시</span></header><div className="table-scroll worksheet-scroll"><table className="worksheet-table"><thead><tr><th scope="col">행</th>{worksheet.columns.map((column) => <th scope="col" key={column.name}><button type="button" onClick={() => setSelectedColumn(column.name)}>{column.name}<small>{column.data_type} · 결측 {column.missing_count}</small></button></th>)}</tr></thead><tbody>{Array.from({ length: visibleRows }, (_, rowIndex) => <tr key={rowIndex}><th scope="row">{rowIndex + 1}</th>{worksheet.columns.map((column) => { const value = column.values[rowIndex]; return <td key={column.name}><button type="button" className="cell-button" onClick={(event) => openEditor(event, { rowIndex, column })} aria-label={`행 ${rowIndex + 1}, 열 ${column.name}, 값 ${value === null ? "결측" : String(value)} 편집`}>{value === null ? <span className="missing-value">—<span className="sr-only">결측</span></span> : String(value)}</button></td>; })}</tr>)}</tbody></table></div>{worksheet.row_count > visibleRows && <p className="table-limit-note">성능 보호를 위해 처음 200행만 표시합니다. 원본에는 {worksheet.row_count}행이 보존됩니다.</p>}</article>
    </section>
    <section className="worksheet-layout" aria-label="작업표 변환">
      <article className="panel"><header className="panel-heading"><div><span className="eyebrow">FILTER ROWS</span><h2>행 필터</h2></div><Filter aria-hidden="true" /></header><p className="supporting-copy">조건에 맞는 행만 남긴 새 revision을 만듭니다. 원본 데이터와 이전 revision은 바뀌지 않습니다.</p><form className="form-stack" onSubmit={handleFilterRows}><label className="field">열<select name="column_name" defaultValue={worksheet.columns[0]?.name}>{worksheet.columns.map((column) => <option key={column.name} value={column.name}>{column.name}</option>)}</select></label><label className="field">조건<select name="operator" defaultValue="equals"><option value="equals">같음</option><option value="not_equals">같지 않음</option><option value="greater_than">초과 (숫자)</option><option value="greater_or_equal">이상 (숫자)</option><option value="less_than">미만 (숫자)</option><option value="less_or_equal">이하 (숫자)</option><option value="contains">포함 (텍스트)</option><option value="is_missing">결측값임</option><option value="is_not_missing">결측값 아님</option></select></label><label className="field">값<input name="value" aria-label="필터 값" /></label><Button type="submit" loading={busy} icon={<Filter />}>필터 revision 저장</Button></form></article>
      <article className="panel"><header className="panel-heading"><div><span className="eyebrow">SORT ROWS</span><h2>행 정렬</h2></div><ListFilter aria-hidden="true" /></header><p className="supporting-copy">결측값은 항상 마지막에 유지하며, 같은 값은 기존 순서를 보존합니다.</p><form className="form-stack" onSubmit={handleSortRows}><label className="field">정렬 열<select name="column_name" defaultValue={worksheet.columns[0]?.name}>{worksheet.columns.map((column) => <option key={column.name} value={column.name}>{column.name}</option>)}</select></label><label className="check-field"><input name="descending" type="checkbox" /><span>내림차순</span></label><Button type="submit" loading={busy} icon={<ListFilter />}>정렬 revision 저장</Button></form></article>
      <article className="panel"><header className="panel-heading"><div><span className="eyebrow">DERIVED NUMERIC COLUMN</span><h2>파생 숫자 열</h2></div><Sigma aria-hidden="true" /></header><p className="supporting-copy">임의 수식은 실행하지 않습니다. 숫자 열의 복사·사칙연산만 새 열로 저장합니다.</p>{numericColumns.length ? <form className="form-stack" onSubmit={handleDerivedColumn}><label className="field">새 열 이름<input name="column_name" required /></label><label className="field">기준 열<select name="source_column" defaultValue={numericColumns[0]?.name}>{numericColumns.map((column) => <option key={column.name} value={column.name}>{column.name}</option>)}</select></label><label className="field">연산<select name="operation" defaultValue="copy"><option value="copy">복사</option><option value="add">더하기</option><option value="subtract">빼기</option><option value="multiply">곱하기</option><option value="divide">나누기</option></select></label><label className="field">피연산자 유형<select name="operand_mode" defaultValue="column"><option value="column">숫자 열</option><option value="constant">상수</option></select></label><label className="field">피연산자 열<select name="operand_column" defaultValue={numericColumns[0]?.name}>{numericColumns.map((column) => <option key={column.name} value={column.name}>{column.name}</option>)}</select></label><label className="field">피연산자 상수<input name="operand_constant" type="number" step="any" defaultValue="1" /></label><Button type="submit" loading={busy} icon={<Sigma />}>파생 열 revision 저장</Button></form> : <p className="state-message">파생 숫자 열에는 하나 이상의 숫자 열이 필요합니다.</p>}</article>
    </section>
    {selectedCell && <><button className="drawer-scrim" type="button" aria-label="셀 편집 닫기" onClick={closeEditor} /><aside ref={drawerRef} className="detail-drawer cell-editor" role="dialog" aria-modal="true" aria-labelledby="cell-editor-title"><header><div><span className="eyebrow">CELL EDIT</span><h2 id="cell-editor-title">{selectedCell.column.name} · 행 {selectedCell.rowIndex + 1}</h2></div><button className="icon-button" type="button" aria-label="닫기" onClick={closeEditor}>×</button></header><form onSubmit={handleSave}><label className="field">새 값<input ref={editorRef} name="value" defaultValue={selectedCell.column.values[selectedCell.rowIndex] === null ? "" : String(selectedCell.column.values[selectedCell.rowIndex])} /><small>빈 값으로 저장하면 결측값이 됩니다. 열 타입은 {selectedCell.column.data_type}입니다.</small></label><Button type="submit" variant="primary" loading={busy} icon={<Save />}>새 revision으로 저장</Button></form><p className="method-note"><Pencil aria-hidden="true" /> 현재 revision은 변경하지 않고 부모 digest가 연결된 새 revision을 생성합니다.</p></aside></>}
  </div>;
}

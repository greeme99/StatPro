import { AlertTriangle, ArrowRight, Database, FileCheck2, FileUp } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { importCsvWorksheet, importParquetWorksheet, importSqliteWorksheet, importXlsxWorksheet, listWorksheets } from "../api";
import { Button } from "../components/Button";
import type { StoredWorksheet } from "../types";

function fileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("데이터 파일을 읽지 못했습니다."));
    reader.onload = () => {
      const result = String(reader.result ?? "");
      const separator = result.indexOf(",");
      if (separator < 0) reject(new Error("데이터 파일 형식을 확인하세요."));
      else resolve(result.slice(separator + 1));
    };
    reader.readAsDataURL(file);
  });
}

export function DataPage() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [worksheets, setWorksheets] = useState<StoredWorksheet[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [selectedSource, setSelectedSource] = useState<"none" | "csv" | "xlsx" | "parquet" | "sqlite">("none");
  const [selectedFileName, setSelectedFileName] = useState("");

  function updateSelectedSource() {
    const fileName = fileRef.current?.files?.[0]?.name ?? "";
    const normalized = fileName.toLowerCase();
    setSelectedFileName(fileName);
    setSelectedSource(normalized.endsWith(".xlsx") ? "xlsx" : /\.(db|sqlite|sqlite3)$/.test(normalized) ? "sqlite" : /\.(parquet|pq)$/.test(normalized) ? "parquet" : normalized.endsWith(".csv") ? "csv" : "none");
  }

  useEffect(() => {
    let active = true;
    listWorksheets()
      .then((page) => { if (active) { setWorksheets(page.items); setState("ready"); } })
      .catch(() => { if (active) setState("error"); });
    return () => { active = false; };
  }, []);

  async function handleImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = fileRef.current?.files?.[0];
    if (!file) { setError("가져올 CSV, XLSX, Parquet 또는 SQLite 파일을 선택하세요."); fileRef.current?.focus(); return; }
    if (!/\.(csv|xlsx|parquet|pq|db|sqlite|sqlite3)$/i.test(file.name)) { setError("CSV, XLSX, Parquet 또는 SQLite 파일만 가져올 수 있습니다."); fileRef.current?.focus(); return; }
    if (file.size > 20_000_000) { setError("데이터 파일은 20MB 이하여야 합니다."); fileRef.current?.focus(); return; }
    const lowerName = file.name.toLowerCase();
    const parquetFile = /\.(parquet|pq)$/.test(lowerName);
    const sqliteFile = /\.(db|sqlite|sqlite3)$/.test(lowerName);
    const tableName = String(form.get("table_name") ?? "").trim();
    if (sqliteFile && !tableName) { setError("SQLite에서 가져올 테이블 이름을 입력하세요."); (event.currentTarget.elements.namedItem("table_name") as HTMLInputElement | null)?.focus(); return; }
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        file_name: file.name,
        worksheet_name: String(form.get("worksheet_name") ?? "").trim(),
        content_base64: await fileAsBase64(file),
      };
      const created = lowerName.endsWith(".xlsx")
        ? await importXlsxWorksheet({ ...payload, sheet_name: String(form.get("sheet_name") ?? "").trim() || undefined })
        : parquetFile
          ? await importParquetWorksheet(payload)
        : sqliteFile
          ? await importSqliteWorksheet({ ...payload, table_name: tableName })
        : await importCsvWorksheet(payload);
      navigate(`/data/${created.worksheet_id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "데이터를 가져오지 못했습니다.");
    } finally { setSubmitting(false); }
  }

  return <div className="page data-page" data-density="compact">
    <section className="page-heading"><div><span className="eyebrow">공유 데이터</span><h1>작업표</h1><p>CSV, XLSX, Parquet 또는 SQLite 원본의 타입·결측 정보를 보존하고 모든 셀 변경을 새 개정으로 기록합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div>}
    <section className="data-list-layout">
      <article className="panel"><header className="panel-heading"><div><span className="eyebrow">작업표 목록</span><h2>저장된 작업표</h2></div><span>{worksheets.length}개</span></header>
        {state === "loading" && <div className="state-message"><p>작업표를 불러오는 중입니다.</p></div>}
        {state === "error" && <div className="state-message is-error"><AlertTriangle aria-hidden="true" /><h3>목록을 불러오지 못했습니다</h3><p>로컬 API 연결을 확인하세요.</p></div>}
        {state === "ready" && worksheets.length === 0 && <div className="state-message"><Database aria-hidden="true" /><h3>저장된 작업표가 없습니다</h3><p>CSV, XLSX, Parquet 또는 SQLite 테이블을 가져오면 타입화된 데이터 표가 만들어집니다.</p></div>}
        {worksheets.length > 0 && <div className="table-scroll"><table><caption className="sr-only">저장된 작업표 목록</caption><thead><tr><th scope="col">이름</th><th scope="col">Revision</th><th scope="col">행</th><th scope="col">열</th><th scope="col"><span className="sr-only">열기</span></th></tr></thead><tbody>{worksheets.map(({ worksheet }) => <tr key={worksheet.worksheet_id}><td><strong>{worksheet.name}</strong><small className="table-subtitle">{worksheet.worksheet_id}</small></td><td>{worksheet.revision}</td><td>{worksheet.row_count}</td><td>{worksheet.columns.length}</td><td><Link className="text-link" to={`/data/${worksheet.worksheet_id}`}>열기 <ArrowRight aria-hidden="true" /></Link></td></tr>)}</tbody></table></div>}
      </article>
      <form className="panel compact-form" onSubmit={handleImport}><header className="panel-heading"><div><span className="eyebrow">데이터 가져오기</span><h2>데이터 가져오기</h2></div><FileUp aria-hidden="true" /></header><div className="form-stack">
        <label className="field">작업표 이름<input name="worksheet_name" required defaultValue="공정 측정값" /></label>
        <label className="field">데이터 파일 (CSV/XLSX/Parquet/SQLite)<input ref={fileRef} name="data_file" type="file" onChange={updateSelectedSource} accept=".csv,text/csv,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,.parquet,.pq,application/vnd.apache.parquet,.db,.sqlite,.sqlite3,application/vnd.sqlite3" /><small>파일을 선택하면 필요한 원본 옵션만 표시합니다. 최대 20MB까지 가져올 수 있습니다.</small></label>
        {selectedFileName && <div className="import-file-summary" role="status"><FileCheck2 aria-hidden="true" /><div><strong>파일 선택됨</strong><span>{selectedFileName} · {selectedSource === "xlsx" ? "XLSX 시트 확인 필요" : selectedSource === "sqlite" ? "SQLite 테이블 이름 필요" : selectedSource === "parquet" ? "Parquet 평면 scalar 데이터" : selectedSource === "csv" ? "CSV 데이터" : "지원 형식을 확인하세요"}</span></div></div>}
        {selectedSource === "xlsx" && <label className="field">XLSX 시트 이름 (선택)<input name="sheet_name" placeholder="비우면 첫 번째 시트" /><small>다중 시트 XLSX는 시트 이름을 정확히 입력하세요.</small></label>}
        {selectedSource === "sqlite" && <label className="field">SQLite 테이블 이름 *<input name="table_name" required placeholder="예: measurements" /><small>저장된 일반 테이블 하나만 읽으며 임의 SQL과 가상 테이블은 실행하지 않습니다.</small></label>}
        {selectedSource === "none" && <p className="import-source-note">UTF-8 CSV, 값 전용 XLSX, 평면 scalar Parquet 또는 SQLite 테이블을 지원합니다. 결측은 보존하며 중첩 Parquet·수식·임의 SQL은 실행하지 않습니다.</p>}
        <Button type="submit" variant="primary" loading={submitting} icon={<FileUp />}>가져오기</Button>
      </div></form>
    </section>
  </div>;
}

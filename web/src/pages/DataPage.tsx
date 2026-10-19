import { AlertTriangle, ArrowRight, Database, FileUp } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { importCsvWorksheet, listWorksheets } from "../api";
import { Button } from "../components/Button";
import type { StoredWorksheet } from "../types";

function fileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("CSV 파일을 읽지 못했습니다."));
    reader.onload = () => {
      const result = String(reader.result ?? "");
      const separator = result.indexOf(",");
      if (separator < 0) reject(new Error("CSV 파일 인코딩을 확인하세요."));
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
    if (!file) { setError("가져올 CSV 파일을 선택하세요."); fileRef.current?.focus(); return; }
    if (file.size > 20_000_000) { setError("CSV 파일은 20MB 이하여야 합니다."); fileRef.current?.focus(); return; }
    setSubmitting(true);
    setError("");
    try {
      const created = await importCsvWorksheet({
        file_name: file.name,
        worksheet_name: String(form.get("worksheet_name") ?? "").trim(),
        content_base64: await fileAsBase64(file),
      });
      navigate(`/data/${created.worksheet_id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "CSV를 가져오지 못했습니다.");
    } finally { setSubmitting(false); }
  }

  return <div className="page data-page" data-density="compact">
    <section className="page-heading"><div><span className="eyebrow">SHARED DATA</span><h1>워크시트</h1><p>CSV 원본과 타입·결측 정보를 보존하고 모든 셀 변경을 새 revision으로 기록합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div>}
    <section className="data-list-layout">
      <article className="panel"><header className="panel-heading"><div><span className="eyebrow">WORKSHEETS</span><h2>저장된 워크시트</h2></div><span>{worksheets.length}개</span></header>
        {state === "loading" && <div className="state-message"><p>워크시트를 불러오는 중입니다.</p></div>}
        {state === "error" && <div className="state-message is-error"><AlertTriangle aria-hidden="true" /><h3>목록을 불러오지 못했습니다</h3><p>로컬 API 연결을 확인하세요.</p></div>}
        {state === "ready" && worksheets.length === 0 && <div className="state-message"><Database aria-hidden="true" /><h3>저장된 워크시트가 없습니다</h3><p>CSV를 가져오면 타입화된 데이터 표가 만들어집니다.</p></div>}
        {worksheets.length > 0 && <div className="table-scroll"><table><thead><tr><th>이름</th><th>Revision</th><th>행</th><th>열</th><th><span className="sr-only">열기</span></th></tr></thead><tbody>{worksheets.map(({ worksheet }) => <tr key={worksheet.worksheet_id}><td><strong>{worksheet.name}</strong><small className="table-subtitle">{worksheet.worksheet_id}</small></td><td>{worksheet.revision}</td><td>{worksheet.row_count}</td><td>{worksheet.columns.length}</td><td><Link className="text-link" to={`/data/${worksheet.worksheet_id}`}>열기 <ArrowRight aria-hidden="true" /></Link></td></tr>)}</tbody></table></div>}
      </article>
      <form className="panel compact-form" onSubmit={handleImport}><header className="panel-heading"><div><span className="eyebrow">IMPORT CSV</span><h2>CSV 가져오기</h2></div><FileUp aria-hidden="true" /></header><div className="form-stack">
        <label className="field">워크시트 이름<input name="worksheet_name" required defaultValue="Process Measurements" /></label>
        <label className="field">CSV 파일<input ref={fileRef} name="csv_file" type="file" accept=".csv,text/csv" /><small>UTF-8 CSV, 최대 20MB. 빈 셀은 결측으로 보존됩니다.</small></label>
        <Button type="submit" variant="primary" loading={submitting} icon={<FileUp />}>가져오기</Button>
      </div></form>
    </section>
  </div>;
}

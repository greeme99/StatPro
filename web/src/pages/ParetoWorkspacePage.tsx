import { FormEvent, useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, BarChart3, Plus, Trash2 } from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { createParetoRun, getCheckSheet } from "../api";

type InputRow = { id: string; category: string; value: string };

const sampleRows: InputRow[] = [
  { id: "sample-1", category: "스크래치", value: "42" },
  { id: "sample-2", category: "오염", value: "25" },
  { id: "sample-3", category: "찍힘", value: "14" },
  { id: "sample-4", category: "조립 불량", value: "9" },
  { id: "sample-5", category: "기타", value: "5" },
];

function emptyRow(index: number): InputRow {
  return { id: `row-${Date.now()}-${index}`, category: "", value: "" };
}

export function ParetoWorkspacePage() {
  const [search] = useSearchParams();
  const sourceSheet = search.get("sourceSheet");
  const navigate = useNavigate();
  const [rows, setRows] = useState<InputRow[]>([emptyRow(1), emptyRow(2), emptyRow(3)]);
  const [subject, setSubject] = useState("품질 문제 우선순위");
  const [metricKind, setMetricKind] = useState<"frequency" | "cost" | "loss">("frequency");
  const [threshold, setThreshold] = useState(80);
  const [sourceDigest, setSourceDigest] = useState<string | null>(null);
  const [state, setState] = useState<"idle" | "loading-source" | "submitting">("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!sourceSheet) return;
    setState("loading-source");
    getCheckSheet(sourceSheet).then((stored) => {
      const frequencies = (stored.summary.tables.frequencies ?? []) as Array<{ category: string; count: number }>;
      setRows(frequencies.map((row, index) => ({ id: `source-${index}`, category: row.category, value: String(row.count) })));
      setSubject(stored.sheet.title);
      setMetricKind("frequency");
      setSourceDigest(stored.sheet.digest);
      setState("idle");
    }).catch((cause) => {
      setError(cause instanceof Error ? cause.message : "체크 시트 집계를 불러오지 못했습니다.");
      setState("idle");
    });
  }, [sourceSheet]);

  const validRows = useMemo(() => rows.filter((row) => row.category.trim() && Number(row.value) >= 0), [rows]);
  const canRun = validRows.length > 0 && validRows.some((row) => Number(row.value) > 0) && state === "idle";

  function updateRow(id: string, field: "category" | "value", value: string) {
    setRows((current) => current.map((row) => row.id === id ? { ...row, [field]: value } : row));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canRun) return;
    setState("submitting");
    setError("");
    try {
      const run = await createParetoRun({
        run_id: `pareto-${Date.now()}`,
        subject,
        metric_kind: metricKind,
        threshold_percentage: threshold,
        items: validRows.map((row) => ({ category: row.category.trim(), value: Number(row.value) })),
        source_sheet_id: sourceSheet,
        source_snapshot_digest: sourceDigest,
      });
      navigate(`/runs/${run.run_id}`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "파레토 분석을 실행하지 못했습니다.");
      setState("idle");
    }
  }

  return <div className="page pareto-workspace" data-density="comfortable">
    <Link className="back-link" to="/spc"><ArrowLeft aria-hidden="true" /> SPC 작업공간</Link>
    <section className="spc-tool-hero"><span className="preview-icon"><BarChart3 aria-hidden="true" /></span><div><span className="eyebrow">PRIORITIZE · INVESTIGATE · ACT</span><h1>파레토 차트(Pareto Chart) 작업공간</h1><p>분류별 빈도·비용·손실을 한 척도로 정렬하고 누적 기여도를 확인해 조사할 문제의 순서를 정합니다.</p></div></section>
    <ol className="spc-process-rail" aria-label="파레토 분석 단계">
      <li><span>1</span><div><strong>설정</strong><p>대상과 기준을 정의합니다.</p></div></li>
      <li><span>2</span><div><strong>데이터</strong><p>분류별 값을 입력합니다.</p></div></li>
      <li><span>3</span><div><strong>분석</strong><p>순위와 누적률을 계산합니다.</p></div></li>
      <li><span>4</span><div><strong>결과</strong><p>핵심 소수를 확인합니다.</p></div></li>
      <li><span>5</span><div><strong>후속 조치</strong><p>원인분석으로 연결합니다.</p></div></li>
    </ol>
    <form className="tool-workspace-panel pareto-form" onSubmit={submit}>
      <header><h2>1. 분석 설정</h2><p>누적 기준은 조사 범위를 좁히는 운영 기준이며 원인이나 인과를 증명하지 않습니다.</p></header>
      {sourceSheet && <p className="spc-evidence-note">체크 시트 <strong>{sourceSheet}</strong>의 현재 스냅샷에서 집계값을 불러왔습니다.</p>}
      <div className="pareto-settings">
        <label>분석 대상<input value={subject} onChange={(event) => setSubject(event.target.value)} required /></label>
        <label>값의 기준<select value={metricKind} onChange={(event) => setMetricKind(event.target.value as typeof metricKind)}><option value="frequency">발생 빈도(Frequency)</option><option value="cost">비용(Cost)</option><option value="loss">손실(Loss)</option></select></label>
        <label>누적 우선 기준(%)<input type="number" min="1" max="100" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} required /></label>
      </div>
      <div className="pareto-data-heading"><div><h2>2. 분류별 데이터</h2><p>같은 의미의 분류는 분석 경계에서 자동 합산됩니다.</p></div><button type="button" className="button button-secondary" onClick={() => { setRows(sampleRows); setSourceDigest(null); }}>예제 데이터 불러오기</button></div>
      <div className="pareto-input-table" role="group" aria-label="파레토 분류별 값 입력">
        <div className="pareto-input-head"><span>분류</span><span>값</span><span>삭제</span></div>
        {rows.map((row, index) => <div className="pareto-input-row" key={row.id}><label><span className="sr-only">{index + 1}번 분류</span><input aria-label={`${index + 1}번 분류`} value={row.category} onChange={(event) => updateRow(row.id, "category", event.target.value)} /></label><label><span className="sr-only">{index + 1}번 값</span><input aria-label={`${index + 1}번 값`} type="number" min="0" step="any" value={row.value} onChange={(event) => updateRow(row.id, "value", event.target.value)} /></label><button type="button" className="icon-button" aria-label={`${index + 1}번 행 삭제`} onClick={() => setRows((current) => current.filter((item) => item.id !== row.id))}><Trash2 aria-hidden="true" /></button></div>)}
      </div>
      <div className="pareto-actions"><button type="button" className="button button-secondary" onClick={() => setRows((current) => [...current, emptyRow(current.length + 1)])}><Plus aria-hidden="true" /> 분류 추가</button><button className="primary-button" type="submit" disabled={!canRun}>{state === "submitting" ? "분석 실행 중…" : <>파레토 분석 실행 <ArrowRight aria-hidden="true" /></>}</button></div>
      {!canRun && state === "idle" && <p className="method-note">한 개 이상의 분류와 양수 값을 입력하면 분석을 실행할 수 있습니다.</p>}
      {state === "loading-source" && <p className="method-note" role="status">체크 시트 집계를 불러오는 중입니다.</p>}
      {error && <p className="error" role="alert">{error}</p>}
    </form>
  </div>;
}

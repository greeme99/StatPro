import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createNestedGageRrRun } from "../api";
import { Button } from "../components/Button";

type Measurement = { part: string; operator: string; measurement: number };
const defaultRunId = () => "gage-rr-nested-" + new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
function parseRecords(source: string): Measurement[] | null {
  const parsed = source.trim().split(/\r?\n/).filter(Boolean).map((row) => row.split(/[,\t;]/).map((cell) => cell.trim()));
  if (parsed[0]?.[0]?.toLowerCase() === "part") parsed.shift();
  if (!parsed.length || parsed.some((row) => row.length !== 3 || !row[0] || !row[1] || !Number.isFinite(Number(row[2])))) return null;
  return parsed.map(([part, operator, measurement]) => ({ part, operator, measurement: Number(measurement) }));
}

export function NestedGageRrSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [recordsText, setRecordsText] = useState("part,operator,measurement\nA1,A,10\nA1,A,12\nA2,A,20\nA2,A,22\nB1,B,12\nB1,B,14\nB2,B,18\nB2,B,20");
  const [multiplier, setMultiplier] = useState("6");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const records = useMemo(() => parseRecords(recordsText), [recordsText]);
  async function submit(event: FormEvent) {
    event.preventDefault();
    const studyVariationMultiplier = Number(multiplier);
    if (!records) { setError("각 행을 부품, 작업자, 측정값의 세 열로 입력하세요. 헤더 행은 선택사항입니다."); textarea.current?.focus(); return; }
    if (!Number.isFinite(studyVariationMultiplier) || studyVariationMultiplier <= 0) { setError("Study variation 배수는 0보다 큰 숫자여야 합니다."); return; }
    setError(""); setLoading(true);
    try { await createNestedGageRrRun({ run_id: runId, records, study_variation_multiplier: studyVariationMultiplier }); navigate("/runs/" + runId); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "중첩 Gage R&R 분석을 실행하지 못했습니다."); textarea.current?.focus(); }
    finally { setLoading(false); }
  }
  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/home/dmaic/measure"><ArrowLeft aria-hidden="true" /> DMAIC 측정(Measure)</Link>
    <section className="page-heading"><div><span className="eyebrow">MSA / NESTED GAGE R&R</span><h1>중첩 Gage R&R 분석 설정</h1><p>파괴검사처럼 모든 작업자가 같은 부품을 측정할 수 없을 때, 작업자 내 고유 부품의 반복 측정으로 변동을 분리합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자와 변동 기준</h2><p>Study variation은 보고 배수이며 원자료나 분산 추정값을 바꾸지 않습니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>Study variation 배수</span><input type="number" min="0.0001" step="any" value={multiplier} onChange={(event) => setMultiplier(event.target.value)} required /></label></div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>중첩 측정 데이터</h2><p>부품 ID는 한 작업자에게만 속해야 합니다. 모든 작업자가 같은 수의 고유 부품을 같은 횟수로 반복 측정해야 합니다.</p></div></header><label className="field"><span>part, operator, measurement *</span><textarea ref={textarea} rows={12} value={recordsText} onChange={(event) => setRecordsText(event.target.value)} aria-invalid={Boolean(error)} /><small>{records ? records.length + "개 측정값 인식됨" : "형식 확인 필요"}</small></label></section>
      <aside className="method-note"><strong>선택 가이드</strong><p>교차 Gage R&R은 모든 작업자가 같은 부품을 측정할 수 있을 때 사용합니다. 부품을 소모하거나 작업자별 시료만 가능한 경우에만 중첩 설계를 사용하며, 부품 내 동질성 가정이 필요합니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>중첩 Gage R&R 분석 실행</Button></div>
    </form>
  </div>;
}

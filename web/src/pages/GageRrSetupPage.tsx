import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createGageRrRun } from "../api";
import { Button } from "../components/Button";

type Measurement = { part: string; operator: string; measurement: number };

function defaultRunId() {
  return "gage-rr-" + new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
}

function parseRecords(source: string): Measurement[] | null {
  const rows = source.trim().split(/\r?\n/).filter(Boolean);
  const parsed = rows.map((row) => row.split(/[,\t;]/).map((cell) => cell.trim()));
  if (parsed[0]?.[0]?.toLowerCase() === "part") parsed.shift();
  if (!parsed.length || parsed.some((row) => row.length !== 3 || !row[0] || !row[1] || !Number.isFinite(Number(row[2])))) return null;
  return parsed.map(([part, operator, measurement]) => ({ part, operator, measurement: Number(measurement) }));
}

export function GageRrSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [recordsText, setRecordsText] = useState("part,operator,measurement\nP1,A,10\nP1,A,12\nP1,B,11\nP1,B,13\nP2,A,20\nP2,A,22\nP2,B,19\nP2,B,21");
  const [multiplier, setMultiplier] = useState("6");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const records = useMemo(() => parseRecords(recordsText), [recordsText]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const studyVariationMultiplier = Number(multiplier);
    if (!records) {
      setError("각 행을 부품, 작업자, 측정값의 세 열로 입력하세요. 헤더 행은 선택사항입니다.");
      textarea.current?.focus();
      return;
    }
    if (!Number.isFinite(studyVariationMultiplier) || studyVariationMultiplier <= 0) {
      setError("Study variation 배수는 0보다 큰 숫자여야 합니다.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createGageRrRun({ run_id: runId, records, study_variation_multiplier: studyVariationMultiplier });
      navigate("/runs/" + runId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "교차 Gage R&R 분석을 실행하지 못했습니다.");
      textarea.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/home/dmaic/measure"><ArrowLeft aria-hidden="true" /> DMAIC 측정(Measure)</Link>
    <section className="page-heading"><div><span className="eyebrow">MSA / GAGE R&R</span><h1>교차 Gage R&R 분석 설정</h1><p>모든 작업자가 모든 부품을 같은 횟수로 측정한 균형 교차 설계에서 반복성과 재현성을 분리합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자와 변동 기준</h2><p>Study variation은 각 분산성분의 보고 기준을 정할 뿐 원자료를 바꾸지 않습니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>Study variation 배수</span><input type="number" min="0.0001" step="any" value={multiplier} onChange={(event) => setMultiplier(event.target.value)} required /></label></div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>교차 측정 데이터</h2><p>CSV, 탭 또는 세미콜론 구분값을 붙여넣습니다. 부품·작업자 조합마다 동일한 반복 수가 필요합니다.</p></div></header><label className="field"><span>part, operator, measurement *</span><textarea ref={textarea} rows={12} value={recordsText} onChange={(event) => setRecordsText(event.target.value)} aria-invalid={Boolean(error)} /><small>{records ? records.length + "개 측정값 인식됨" : "형식 확인 필요"}</small></label></section>
      <aside className="method-note"><strong>설계 확인</strong><p>교차 Gage R&R은 부품·작업자·상호작용을 랜덤 효과로 추정합니다. 측정 중 공정이 안정적이고, 잔차가 독립·등분산이며, 반복 수가 모든 교차 셀에서 같아야 합니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>Gage R&R 분석 실행</Button></div>
    </form>
  </div>;
}

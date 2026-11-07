import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createGageBiasLinearityRun } from "../api";
import { Button } from "../components/Button";

type Measurement = { reference: number; measurement: number };

function defaultRunId() {
  return "gage-bias-linearity-" + new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
}

function parseRecords(source: string): Measurement[] | null {
  const rows = source.trim().split(/\r?\n/).filter(Boolean);
  const parsed = rows.map((row) => row.split(/[,\t;]/).map((cell) => cell.trim()));
  if (parsed[0]?.[0]?.toLowerCase() === "reference") parsed.shift();
  if (!parsed.length || parsed.some((row) => row.length !== 2 || !Number.isFinite(Number(row[0])) || !Number.isFinite(Number(row[1])))) return null;
  return parsed.map(([reference, measurement]) => ({ reference: Number(reference), measurement: Number(measurement) }));
}

export function GageBiasLinearitySetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [recordsText, setRecordsText] = useState("reference,measurement\n10,10.2\n10,10.1\n20,20.5\n20,20.4\n30,30.8\n30,30.7");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const records = useMemo(() => parseRecords(recordsText), [recordsText]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!records) {
      setError("각 행을 기준값, 측정값의 두 열로 입력하세요. 헤더 행은 선택사항입니다.");
      textarea.current?.focus();
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createGageBiasLinearityRun({ run_id: runId, records });
      navigate("/runs/" + runId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "편의·선형성 분석을 실행하지 못했습니다.");
      textarea.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/home/dmaic/measure"><ArrowLeft aria-hidden="true" /> DMAIC 측정(Measure)</Link>
    <section className="page-heading"><div><span className="eyebrow">MSA / BIAS & LINEARITY</span><h1>Gage 편의·선형성 분석 설정</h1><p>추적 가능한 기준값 범위에서 측정기가 얼마나 높거나 낮게 읽는지와 그 편의의 변화 추세를 확인합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>분석 실행 식별자</h2><p>Run ID로 교정 검토 결과를 FMEA·관리계획의 측정 근거와 연결합니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>기준값과 반복 측정값</h2><p>CSV, 탭 또는 세미콜론 구분값을 붙여넣습니다. 최소 두 기준값이 필요하고 각 기준값은 두 번 이상 반복 측정해야 합니다.</p></div></header><label className="field"><span>reference, measurement *</span><textarea ref={textarea} rows={12} value={recordsText} onChange={(event) => setRecordsText(event.target.value)} aria-invalid={Boolean(error)} /><small>{records ? records.length + "개 측정값 인식됨" : "형식 확인 필요"}</small></label></section>
      <aside className="method-note"><strong>선택 가이드</strong><p>마스터·표준기로 정해진 연속 기준값이 있을 때 사용합니다. 편의는 관측값−기준값으로 계산되어 양수면 높게 읽음을 뜻합니다. 이 화면은 설명적 적합만 제공하므로 교정 승인에는 별도의 신뢰구간·유의성 검토가 필요합니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>편의·선형성 분석 실행</Button></div>
    </form>
  </div>;
}

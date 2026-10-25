import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createCusumRun } from "../api";
import { Button } from "../components/Button";

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `cusum-${timestamp}`;
}

function optionalNumber(text: string) {
  return text.trim() === "" ? undefined : Number(text);
}

export function CusumSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [valuesText, setValuesText] = useState("50 50 50 50 50 51 51 51 51 51 51 51 51 51");
  const [targetText, setTargetText] = useState("50");
  const [sigmaText, setSigmaText] = useState("1");
  const [referenceText, setReferenceText] = useState("0.5");
  const [intervalText, setIntervalText] = useState("4");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const values = valuesText.split(/[\s,;]+/).filter(Boolean).map(Number);
    const target = optionalNumber(targetText);
    const sigma = optionalNumber(sigmaText);
    const referenceValue = Number(referenceText);
    const decisionInterval = Number(intervalText);
    if (values.length < 2 || values.some((value) => !Number.isFinite(value))) {
      setError("시간 순서의 유한 측정값을 두 개 이상 입력하세요.");
      return;
    }
    if (!Number.isFinite(referenceValue) || referenceValue < 0 || !Number.isFinite(decisionInterval) || decisionInterval <= 0 || decisionInterval > 100) {
      setError("참조값 k는 0 이상, 판정구간 h는 0 초과 100 이하로 입력하세요.");
      return;
    }
    if ((target !== undefined && !Number.isFinite(target)) || (sigma !== undefined && (!Number.isFinite(sigma) || sigma <= 0))) {
      setError("과거 평균은 유한 숫자, 과거 σ는 0보다 큰 유한 숫자이거나 빈 값이어야 합니다.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createCusumRun({ run_id: runId, values, target, sigma, reference_value: referenceValue, decision_interval: decisionInterval });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "CUSUM 분석을 실행하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">SPC / TIME-WEIGHTED CHART</span><h1>CUSUM 관리도</h1><p>표준화한 상·하 누적합으로 작은 공정 평균 이동을 감시합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>불변 Analysis Run ID를 지정합니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>시간 순서 측정값</h2><p>쉼표나 공백으로 구분하며 수집 순서를 유지합니다.</p></div></header><label className="field"><span>측정값</span><textarea rows={7} value={valuesText} onChange={(event) => setValuesText(event.target.value)} required /></label></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>기준 모수</h2><p>안정된 과거 평균과 σ를 권장합니다. 비우면 현재 데이터에서 추정합니다.</p></div></header><div className="field-grid"><label className="field"><span>과거 평균 · 선택</span><input inputMode="decimal" value={targetText} onChange={(event) => setTargetText(event.target.value)} /></label><label className="field"><span>과거 σ · 선택</span><input inputMode="decimal" value={sigmaText} onChange={(event) => setSigmaText(event.target.value)} /></label></div></section>
      <section className="form-panel"><header><span className="step-index">04</span><div><h2>CUSUM 계획</h2><p>k와 h는 공정 σ 단위입니다.</p></div></header><div className="field-grid"><label className="field"><span>참조값 k</span><input type="number" min="0" max="10" step="0.1" value={referenceText} onChange={(event) => setReferenceText(event.target.value)} required /></label><label className="field"><span>판정구간 h</span><input type="number" min="0.1" max="100" step="0.1" value={intervalText} onChange={(event) => setIntervalText(event.target.value)} required /></label></div></section>
      <aside className="method-note"><strong>해석 경계</strong><p>상·하 누적합은 0에서 시작하고 판정구간을 초과할 때 신호를 냅니다. 신호는 특별원인 확정이 아니라 조사 후보입니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>CUSUM 실행</Button></div>
    </form>
  </div>;
}

import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createEwmaRun } from "../api";
import { Button } from "../components/Button";

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `ewma-${timestamp}`;
}

function optionalNumber(text: string) {
  return text.trim() === "" ? undefined : Number(text);
}

export function EwmaSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [valuesText, setValuesText] = useState("50 50 50 50 50 51 51 52 52 52 52 52");
  const [targetText, setTargetText] = useState("50");
  const [sigmaText, setSigmaText] = useState("1");
  const [weightText, setWeightText] = useState("0.2");
  const [limitWidthText, setLimitWidthText] = useState("3");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const values = valuesText.split(/[\s,;]+/).filter(Boolean).map(Number);
    const target = optionalNumber(targetText);
    const sigma = optionalNumber(sigmaText);
    const weight = Number(weightText);
    const limitWidth = Number(limitWidthText);
    if (values.length < 2 || values.some((value) => !Number.isFinite(value))) {
      setError("시간 순서의 유한 측정값을 두 개 이상 입력하세요.");
      return;
    }
    if (!Number.isFinite(weight) || weight <= 0 || weight > 1 || !Number.isFinite(limitWidth) || limitWidth <= 0 || limitWidth > 10) {
      setError("EWMA 가중치는 0 초과 1 이하, 한계 폭은 0 초과 10 이하로 입력하세요.");
      return;
    }
    if ((target !== undefined && !Number.isFinite(target)) || (sigma !== undefined && (!Number.isFinite(sigma) || sigma <= 0))) {
      setError("과거 평균은 유한 숫자, 과거 σ는 0보다 큰 유한 숫자이거나 빈 값이어야 합니다.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createEwmaRun({ run_id: runId, values, target, sigma, weight, limit_width: limitWidth });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "EWMA 분석을 실행하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">SPC / TIME-WEIGHTED CHART</span><h1>EWMA 관리도</h1><p>과거 관측값의 영향을 지수적으로 줄여 작은 공정 평균 이동을 감시합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>불변 Analysis Run ID를 지정합니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>시간 순서 측정값</h2><p>쉼표나 공백으로 구분하며 수집 순서를 유지합니다.</p></div></header><label className="field"><span>측정값</span><textarea rows={7} value={valuesText} onChange={(event) => setValuesText(event.target.value)} required /></label></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>기준 모수</h2><p>안정된 과거 평균과 σ를 권장합니다. 비우면 현재 데이터에서 추정합니다.</p></div></header><div className="field-grid"><label className="field"><span>과거 평균 · 선택</span><input inputMode="decimal" value={targetText} onChange={(event) => setTargetText(event.target.value)} /></label><label className="field"><span>과거 σ · 선택</span><input inputMode="decimal" value={sigmaText} onChange={(event) => setSigmaText(event.target.value)} /></label></div></section>
      <section className="form-panel"><header><span className="step-index">04</span><div><h2>검출 민감도</h2><p>가중치가 작을수록 과거 정보를 오래 유지합니다.</p></div></header><div className="field-grid"><label className="field"><span>EWMA 가중치 λ</span><input type="number" min="0.01" max="1" step="0.01" value={weightText} onChange={(event) => setWeightText(event.target.value)} required /></label><label className="field"><span>관리한계 폭 L</span><input type="number" min="0.1" max="10" step="0.1" value={limitWidthText} onChange={(event) => setLimitWidthText(event.target.value)} required /></label></div></section>
      <aside className="method-note"><strong>해석 경계</strong><p>시작 시점 보정 관리한계를 사용합니다. 신호는 특별원인 확정이 아니라 조사 후보이며, 기준 모수는 안정된 과거 데이터에서 정하는 것이 원칙입니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>EWMA 실행</Button></div>
    </form>
  </div>;
}

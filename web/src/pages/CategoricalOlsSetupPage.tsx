import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { type FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createCategoricalOlsRun } from "../api";
import { Button } from "../components/Button";

const toNumbers = (text: string) => text.split(/[\s,;]+/).filter(Boolean).map(Number);
const toLevels = (text: string) => text.split(/[\n,;]+/).map((value) => value.trim()).filter(Boolean);
const runId = () => `categorical-ols-${new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14)}`;

export function CategoricalOlsSetupPage() {
  const navigate = useNavigate();
  const responseRef = useRef<HTMLTextAreaElement>(null);
  const [id, setId] = useState(runId);
  const [responseName, setResponseName] = useState("수율");
  const [response, setResponse] = useState("98.7\n99.2\n101.4\n100.8\n98.9\n99.5\n101.8\n101.1");
  const [predictorName, setPredictorName] = useState("생산 라인");
  const [levelsText, setLevelsText] = useState("A\nA\nB\nB\nA\nA\nB\nB");
  const [reference, setReference] = useState("A");
  const [alpha, setAlpha] = useState("0.05");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const values = useMemo(() => toNumbers(response), [response]);
  const levels = useMemo(() => toLevels(levelsText), [levelsText]);
  const availableLevels = useMemo(() => [...new Set(levels)].sort((left, right) => left.localeCompare(right, "ko-KR")), [levels]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const alphaValue = Number(alpha);
    if (values.length < 3 || values.some((value) => !Number.isFinite(value)) || levels.length !== values.length || availableLevels.length < 2 || !predictorName.trim() || !reference || !availableLevels.includes(reference) || !Number.isFinite(alphaValue) || alphaValue < 0.001 || alphaValue > 0.5) {
      setError("Y는 유한한 숫자 3개 이상, 범주형 X는 같은 행 수의 2개 이상 범주, 기준 범주와 0.001~0.5의 유의수준이 필요합니다.");
      responseRef.current?.focus();
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createCategoricalOlsRun({ run_id: id, response: values, predictors: { [predictorName.trim()]: levels }, reference_levels: { [predictorName.trim()]: reference }, response_name: responseName.trim() || "Response", alpha: alphaValue });
      navigate(`/runs/${id}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석을 실행하지 못했습니다.");
      responseRef.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/analyses"><ArrowLeft aria-hidden="true" /> 분석 선택</Link>
    <section className="page-heading"><div><span className="eyebrow">CATEGORICAL REGRESSION</span><h1>범주형 OLS 회귀 설정</h1><p>생산 라인·설비·작업조처럼 구분값으로 기록된 X를 명시한 기준 범주와 비교해 연속형 결과(Y)의 차이를 추정합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>분석 실행 정보</h2><p>기준 범주를 고정해 결과 계수의 비교 기준을 보존합니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={id} onChange={(event) => setId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>응답변수 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label><label className="field"><span>유의수준 α</span><input type="number" step="0.001" min="0.001" max="0.5" value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label></div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>응답변수(Y)</h2><p>줄바꿈·쉼표·공백으로 구분한 연속형 측정값을 입력합니다.</p></div></header><label className="field"><span>응답값(Y) *</span><textarea ref={responseRef} rows={8} value={response} onChange={(event) => setResponse(event.target.value)} /><small>{values.filter(Number.isFinite).length}개 값 인식됨</small></label></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>범주형 설명변수(X)</h2><p>한 줄은 Y의 같은 행에 대응합니다. 공백이 포함된 범주는 줄바꿈으로 구분하세요.</p></div></header><div className="inline-fields"><label className="field"><span>설명변수 이름</span><input value={predictorName} onChange={(event) => setPredictorName(event.target.value)} required /></label><label className="field"><span>기준 범주</span><select aria-label="기준 범주" value={availableLevels.includes(reference) ? reference : ""} onChange={(event) => setReference(event.target.value)} required><option value="" disabled>기준 범주 선택</option>{availableLevels.map((level) => <option value={level} key={level}>{level}</option>)}</select><small>계수는 이 범주와 비교됩니다.</small></label></div><label className="field"><span>{predictorName.trim() || "설명변수"} 범주(X) *</span><textarea rows={8} value={levelsText} onChange={(event) => setLevelsText(event.target.value)} /><small>{levels.length}개 값 · {availableLevels.length}개 범주 인식됨 · Y {values.length}개와 같아야 합니다.</small></label></section>
      <aside className="method-note"><strong>해석 전 확인</strong><p>범주형 OLS는 각 수준의 평균 차이를 기준 범주와 비교합니다. 범주별 충분한 표본 수, 독립성·등분산성·잔차를 확인하고 유의성만으로 현장 조건을 확정하지 마세요.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>범주형 OLS 회귀 실행</Button></div>
    </form>
  </div>;
}

import { AlertTriangle, ArrowLeft, Plus, Play, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createCategoricalOlsRun } from "../api";
import { Button } from "../components/Button";

type CategoricalPredictor = { id: number; name: string; levelsText: string; reference: string };

const toNumbers = (text: string) => text.split(/[\s,;]+/).filter(Boolean).map(Number);
const toLevels = (text: string) => text.split(/[\n,;]+/).map((value) => value.trim()).filter(Boolean);
const runId = () => `categorical-ols-${new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14)}`;
const initialPredictor = (): CategoricalPredictor => ({ id: 1, name: "생산 라인", levelsText: "A\nA\nB\nB\nA\nA\nB\nB", reference: "A" });

export function CategoricalOlsSetupPage() {
  const navigate = useNavigate();
  const responseRef = useRef<HTMLTextAreaElement>(null);
  const [id, setId] = useState(runId);
  const [responseName, setResponseName] = useState("수율");
  const [response, setResponse] = useState("98.7\n99.2\n101.4\n100.8\n98.9\n99.5\n101.8\n101.1");
  const [predictors, setPredictors] = useState<CategoricalPredictor[]>([initialPredictor()]);
  const [alpha, setAlpha] = useState("0.05");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const values = useMemo(() => toNumbers(response), [response]);
  const resolvedPredictors = useMemo(() => predictors.map((predictor) => {
    const levels = toLevels(predictor.levelsText);
    return { ...predictor, levels, availableLevels: [...new Set(levels)].sort((left, right) => left.localeCompare(right, "ko-KR")) };
  }), [predictors]);
  const expandedTermCount = resolvedPredictors.reduce((total, predictor) => total + Math.max(0, predictor.availableLevels.length - 1), 0);

  function updatePredictor(predictorId: number, field: keyof Omit<CategoricalPredictor, "id">, value: string) {
    setPredictors((current) => current.map((predictor) => predictor.id === predictorId ? { ...predictor, [field]: value } : predictor));
  }

  function addPredictor() {
    setPredictors((current) => [...current, { id: Math.max(...current.map((predictor) => predictor.id)) + 1, name: `범주형 변수 ${current.length + 1}`, levelsText: "", reference: "" }]);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const alphaValue = Number(alpha);
    const names = resolvedPredictors.map((predictor) => predictor.name.trim());
    const validPredictors = names.every((name, index) => name && names.indexOf(name) === index && resolvedPredictors[index].levels.length === values.length && resolvedPredictors[index].availableLevels.length >= 2 && resolvedPredictors[index].availableLevels.includes(resolvedPredictors[index].reference));
    if (values.length < 3 || values.some((value) => !Number.isFinite(value)) || !validPredictors || expandedTermCount > 20 || values.length <= expandedTermCount + 1 || !Number.isFinite(alphaValue) || alphaValue < 0.001 || alphaValue > 0.5) {
      setError("Y는 유한한 숫자여야 하며, 각 범주형 X는 같은 행 수의 2개 이상 범주와 기준 범주가 필요합니다. 이름은 중복될 수 없고 확장 항은 20개 이하이며 잔차 자유도가 남아야 합니다.");
      responseRef.current?.focus();
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createCategoricalOlsRun({ run_id: id, response: values, predictors: Object.fromEntries(resolvedPredictors.map((predictor) => [predictor.name.trim(), predictor.levels])), reference_levels: Object.fromEntries(resolvedPredictors.map((predictor) => [predictor.name.trim(), predictor.reference])), response_name: responseName.trim() || "Response", alpha: alphaValue });
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
    <section className="page-heading"><div><span className="eyebrow">CATEGORICAL REGRESSION</span><h1>범주형 OLS 회귀 설정</h1><p>생산 라인·설비·작업조처럼 구분값으로 기록된 여러 X를 각각의 기준 범주와 비교해 연속형 결과(Y)의 차이를 추정합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>분석 실행 정보</h2><p>변수별 기준 범주를 고정해 결과 계수의 비교 기준을 보존합니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={id} onChange={(event) => setId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>응답변수 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label><label className="field"><span>유의수준 α</span><input type="number" step="0.001" min="0.001" max="0.5" value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label></div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>응답변수(Y)</h2><p>줄바꿈·쉼표·공백으로 구분한 연속형 측정값을 입력합니다.</p></div></header><label className="field"><span>응답값(Y) *</span><textarea ref={responseRef} rows={8} value={response} onChange={(event) => setResponse(event.target.value)} /><small>{values.filter(Number.isFinite).length}개 값 인식됨</small></label></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>범주형 설명변수(X)</h2><p>한 줄은 Y의 같은 행에 대응합니다. 현재 {predictors.length}개 X와 기준 대비 {expandedTermCount}개 추정 항을 준비했습니다.</p></div></header>{resolvedPredictors.map((predictor, index) => <section className="form-panel" key={predictor.id}><header><h3>범주형 변수 {index + 1}</h3>{predictors.length > 1 && <Button type="button" variant="ghost" icon={<Trash2 aria-hidden="true" />} onClick={() => setPredictors((current) => current.filter((item) => item.id !== predictor.id))}>삭제</Button>}</header><div className="inline-fields"><label className="field"><span>설명변수 이름</span><input value={predictor.name} onChange={(event) => updatePredictor(predictor.id, "name", event.target.value)} required /></label><label className="field"><span>기준 범주</span><select aria-label={`${predictor.name || `범주형 변수 ${index + 1}`} 기준 범주`} value={predictor.availableLevels.includes(predictor.reference) ? predictor.reference : ""} onChange={(event) => updatePredictor(predictor.id, "reference", event.target.value)} required><option value="" disabled>기준 범주 선택</option>{predictor.availableLevels.map((level) => <option value={level} key={level}>{level}</option>)}</select><small>계수는 이 범주와 비교됩니다.</small></label></div><label className="field"><span>{predictor.name.trim() || `범주형 변수 ${index + 1}`} 범주(X) *</span><textarea rows={8} value={predictor.levelsText} onChange={(event) => updatePredictor(predictor.id, "levelsText", event.target.value)} /><small>{predictor.levels.length}개 값 · {predictor.availableLevels.length}개 범주 인식됨 · Y {values.length}개와 같아야 합니다.</small></label></section>)}<div className="form-actions">{predictors.length < 20 && <Button type="button" variant="secondary" icon={<Plus aria-hidden="true" />} onClick={addPredictor}>범주형 변수 추가</Button>}</div></section>
      <aside className="method-note"><strong>해석 전 확인</strong><p>범주형 OLS는 모든 다른 X가 고정된 상태에서 각 수준의 평균 차이를 해당 기준 범주와 비교합니다. 범주별 표본 수, 독립성·등분산성·잔차를 확인하고 유의성만으로 현장 조건을 확정하지 마세요.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>범주형 OLS 회귀 실행</Button></div>
    </form>
  </div>;
}

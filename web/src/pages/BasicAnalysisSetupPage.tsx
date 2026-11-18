import { AlertTriangle, ArrowLeft, Plus, Play, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { createJarqueBeraNormalityRun, createLinearOlsRun } from "../api";
import { Button } from "../components/Button";

type PredictorInput = { id: number; name: string; values: string };

const numbers = (text: string) => text.split(/[\s,;]+/).filter(Boolean).map(Number);
const id = (prefix: string) => `${prefix}-${new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14)}`;
const initialPredictor = (): PredictorInput => ({ id: 1, name: "온도", values: "180\n185\n190\n195\n200\n205" });

export function BasicAnalysisSetupPage() {
  const normality = useLocation().pathname.endsWith("/normality");
  const navigate = useNavigate();
  const [runId, setRunId] = useState(id(normality ? "normality" : "regression"));
  const [values, setValues] = useState("98.7\n99.2\n100.1\n99.5\n100.4\n101.0");
  const [responseName, setResponseName] = useState("수율");
  const [predictors, setPredictors] = useState<PredictorInput[]>([initialPredictor()]);
  const [alpha, setAlpha] = useState("0.05");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const valuesRef = useRef<HTMLTextAreaElement>(null);
  const parsed = useMemo(() => numbers(values), [values]);
  const predictorColumns = useMemo(() => predictors.map((predictor) => ({ ...predictor, parsed: numbers(predictor.values) })), [predictors]);

  function updatePredictor(predictorId: number, field: "name" | "values", value: string) {
    setPredictors((current) => current.map((predictor) => predictor.id === predictorId ? { ...predictor, [field]: value } : predictor));
  }

  function addPredictor() {
    setPredictors((current) => [...current, { id: Math.max(0, ...current.map((predictor) => predictor.id)) + 1, name: `설명변수 ${current.length + 1}`, values: "" }]);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const alphaValue = Number(alpha);
    if (parsed.length < 3 || parsed.some((value) => !Number.isFinite(value)) || !Number.isFinite(alphaValue) || !(alphaValue >= 0.001 && alphaValue <= 0.5)) {
      setError("유한한 숫자 3개 이상과 0.001~0.5 사이의 유의수준을 입력하세요.");
      valuesRef.current?.focus();
      return;
    }
    const names = predictorColumns.map((predictor) => predictor.name.trim());
    const uniqueNames = new Set(names.map((name) => name.toLocaleLowerCase("ko-KR")));
    if (!normality && (names.some((name) => !name) || uniqueNames.size !== names.length || predictorColumns.some((predictor) => predictor.parsed.length !== parsed.length || predictor.parsed.some((value) => !Number.isFinite(value))))) {
      setError("설명변수 이름은 서로 달라야 하며, 모든 X 값은 응답값과 같은 개수의 유한한 숫자여야 합니다.");
      return;
    }
    if (!normality && parsed.length <= predictorColumns.length + 1) {
      setError("회귀는 절편과 설명변수를 추정한 뒤에도 최소 1개의 잔차 자유도가 필요합니다. 관측값을 늘리거나 설명변수를 줄이세요.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      if (normality) {
        await createJarqueBeraNormalityRun({ run_id: runId, values: parsed, alpha: alphaValue });
      } else {
        await createLinearOlsRun({
          run_id: runId,
          response: parsed,
          predictors: Object.fromEntries(predictorColumns.map((predictor) => [predictor.name.trim(), predictor.parsed])),
          response_name: responseName.trim() || "Response",
          alpha: alphaValue,
        });
      }
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석을 실행하지 못했습니다.");
      valuesRef.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  const title = normality ? "정규성 검정 설정" : "선형회귀 분석 설정";
  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/analyses"><ArrowLeft aria-hidden="true" /> 분석 선택</Link>
    <section className="page-heading"><div><span className="eyebrow">STATISTICAL ANALYSIS</span><h1>{title}</h1><p>{normality ? "Jarque–Bera 검정으로 데이터의 정규성 가정을 점검합니다." : "연속형 결과(Y)와 하나 이상의 설명변수(X) 관계를 OLS로 추정합니다."}</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>분석 실행 정보</h2><p>분석 실행은 입력값과 엔진 버전을 고정해 보존합니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>유의수준 α</span><input type="number" step="0.001" min="0.001" max="0.5" value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label>{!normality && <label className="field"><span>응답변수 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label>}</div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>{normality ? "검정할 측정값" : "응답변수(Y)"}</h2><p>줄바꿈·쉼표·공백으로 구분한 숫자를 입력합니다. 결측값을 0으로 대체하지 않습니다.</p></div></header><label className="field"><span>{normality ? "측정값 *" : "응답값(Y) *"}</span><textarea ref={valuesRef} rows={8} value={values} onChange={(event) => setValues(event.target.value)} /><small>{parsed.filter(Number.isFinite).length}개 값 인식됨</small></label></section>
      {!normality && <section className="form-panel"><header><span className="step-index">03</span><div><h2>설명변수(X)</h2><p>각 X는 응답값과 같은 행 순서·개수로 입력합니다. 엔진은 최대 20개 변수를 지원합니다.</p></div></header>{predictorColumns.map((predictor, index) => <div className="form-panel" key={predictor.id}><header><h3>설명변수 {index + 1}</h3>{predictors.length > 1 && <Button type="button" variant="ghost" onClick={() => setPredictors((current) => current.filter((item) => item.id !== predictor.id))} icon={<Trash2 aria-hidden="true" />}>삭제</Button>}</header><div className="inline-fields"><label className="field"><span>설명변수 이름</span><input value={predictor.name} onChange={(event) => updatePredictor(predictor.id, "name", event.target.value)} required /></label></div><label className="field"><span>{predictor.name.trim() || `설명변수 ${index + 1}`} 값(X) *</span><textarea rows={8} value={predictor.values} onChange={(event) => updatePredictor(predictor.id, "values", event.target.value)} /><small>{predictor.parsed.filter(Number.isFinite).length}개 값 인식됨 · 응답값 {parsed.length}개 필요</small></label></div>)}<div className="form-actions">{predictors.length < 20 && <Button type="button" variant="secondary" onClick={addPredictor} icon={<Plus aria-hidden="true" />}>설명변수 추가</Button>}</div></section>}
      <aside className="method-note"><strong>해석 전 확인</strong><p>{normality ? "Jarque–Bera는 점근 카이제곱 근사를 사용합니다. 작은 표본에서는 결과를 단독 확정 근거로 사용하지 마세요." : "OLS는 독립성·선형성·등분산성과 잔차 검토가 필요합니다. 유의성만으로 운영 설정을 확정하지 말고 공정 제약과 확인 실험을 함께 검토하세요."}</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>{normality ? "정규성 검정 실행" : "선형회귀 분석 실행"}</Button></div>
    </form>
  </div>;
}

import { AlertTriangle, ArrowLeft, Plus, Play, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { createBestSubsetsOlsRun, createInteractionOlsRun, createJarqueBeraNormalityRun, createLinearOlsRun, createLogisticRegressionRun, createOlsValidationRun, createPoissonRegressionRun, createPolynomialOlsRun, createStepwiseOlsRun } from "../api";
import { Button } from "../components/Button";

type PredictorInput = { id: number; name: string; values: string };

const numbers = (text: string) => text.split(/[\s,;]+/).filter(Boolean).map(Number);
const id = (prefix: string) => `${prefix}-${new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14)}`;
const initialPredictor = (): PredictorInput => ({ id: 1, name: "온도", values: "180\n185\n190\n195\n200\n205" });
const interactionPredictor = (): PredictorInput => ({ id: 2, name: "압력", values: "1\n2\n1\n2\n1\n2" });

export function BasicAnalysisSetupPage() {
  const normality = useLocation().pathname.endsWith("/normality");
  const polynomial = useLocation().pathname.endsWith("/polynomial");
  const interaction = useLocation().pathname.endsWith("/interaction");
  const stepwise = useLocation().pathname.endsWith("/stepwise");
  const validation = useLocation().pathname.endsWith("/validation");
  const bestSubsets = useLocation().pathname.endsWith("/best-subsets");
  const poisson = useLocation().pathname.endsWith("/poisson");
  const logistic = useLocation().pathname.endsWith("/logistic");
  const navigate = useNavigate();
  const [runId, setRunId] = useState(id(normality ? "normality" : logistic ? "logistic" : poisson ? "poisson" : polynomial ? "polynomial" : interaction ? "interaction" : stepwise ? "stepwise" : validation ? "validation" : bestSubsets ? "best-subsets" : "regression"));
  const [values, setValues] = useState(logistic ? "0\n1\n0\n1\n1\n0\n1\n0" : poisson ? "1\n2\n3\n5\n8\n13" : "98.7\n99.2\n100.1\n99.5\n100.4\n101.0");
  const [responseName, setResponseName] = useState("수율");
  const [predictors, setPredictors] = useState<PredictorInput[]>(() => interaction ? [initialPredictor(), interactionPredictor()] : [initialPredictor()]);
  const [alpha, setAlpha] = useState("0.05");
  const [degree, setDegree] = useState<2 | 3>(2);
  const [selectionMethod, setSelectionMethod] = useState<"forward" | "backward" | "stepwise">("stepwise");
  const [selectionCriterion, setSelectionCriterion] = useState<"aicc" | "bic">("aicc");
  const [includeInteractions, setIncludeInteractions] = useState(false);
  const [validationMethod, setValidationMethod] = useState<"k_fold" | "holdout">("k_fold");
  const [validationFolds, setValidationFolds] = useState(5);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const valuesRef = useRef<HTMLTextAreaElement>(null);
  const parsed = useMemo(() => numbers(values), [values]);
  const predictorColumns = useMemo(() => predictors.map((predictor) => ({ ...predictor, parsed: numbers(predictor.values) })), [predictors]);
  const includesTwoFactorInteractions = interaction || (stepwise && includeInteractions);
  const expandedTermCount = includesTwoFactorInteractions ? predictorColumns.length + (predictorColumns.length * (predictorColumns.length - 1)) / 2 : predictorColumns.length * (polynomial ? degree : 1);
  const maximumPredictors = includesTwoFactorInteractions ? 5 : Math.floor(20 / (polynomial ? degree : 1));

  function updatePredictor(predictorId: number, field: "name" | "values", value: string) {
    setPredictors((current) => current.map((predictor) => predictor.id === predictorId ? { ...predictor, [field]: value } : predictor));
  }

  function addPredictor() {
    setPredictors((current) => [...current, { id: Math.max(0, ...current.map((predictor) => predictor.id)) + 1, name: `설명변수 ${current.length + 1}`, values: "" }]);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const alphaValue = Number(alpha);
    if (parsed.length < (logistic || poisson ? 4 : 3) || parsed.some((value) => !Number.isFinite(value)) || (logistic && parsed.some((value) => value !== 0 && value !== 1)) || (poisson && parsed.some((value) => value < 0 || !Number.isInteger(value))) || !Number.isFinite(alphaValue) || !(alphaValue >= 0.001 && alphaValue <= 0.5)) {
      setError(poisson ? "Poisson 회귀에는 0 이상 정수인 건수 4개 이상과 0.001~0.5 사이의 유의수준을 입력하세요." : "유한한 숫자 3개 이상과 0.001~0.5 사이의 유의수준을 입력하세요.");
      valuesRef.current?.focus();
      return;
    }
    const names = predictorColumns.map((predictor) => predictor.name.trim());
    const uniqueNames = new Set(names.map((name) => name.toLocaleLowerCase("ko-KR")));
    if (!normality && (names.some((name) => !name) || uniqueNames.size !== names.length || predictorColumns.some((predictor) => predictor.parsed.length !== parsed.length || predictor.parsed.some((value) => !Number.isFinite(value))))) {
      setError("설명변수 이름은 서로 달라야 하며, 모든 X 값은 응답값과 같은 개수의 유한한 숫자여야 합니다.");
      return;
    }
    if (interaction && predictorColumns.length < 2) {
      setError("교호작용 회귀는 결합 효과를 추정할 서로 다른 설명변수 2개 이상이 필요합니다.");
      return;
    }
    if (!normality && parsed.length <= expandedTermCount + 1) {
      setError("회귀는 절편과 설명변수 항을 추정한 뒤에도 최소 1개의 잔차 자유도가 필요합니다. 관측값을 늘리거나 설명변수 또는 차수를 줄이세요.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      if (normality) {
        await createJarqueBeraNormalityRun({ run_id: runId, values: parsed, alpha: alphaValue });
      } else {
        const payload = {
          run_id: runId,
          response: parsed,
          predictors: Object.fromEntries(predictorColumns.map((predictor) => [predictor.name.trim(), predictor.parsed])),
          response_name: responseName.trim() || "Response",
          alpha: alphaValue,
        }; if (logistic) await createLogisticRegressionRun(payload); else if (poisson) await createPoissonRegressionRun(payload); else if (polynomial) await createPolynomialOlsRun({ ...payload, degree }); else if (interaction) await createInteractionOlsRun(payload); else if (stepwise) await createStepwiseOlsRun({ ...payload, interaction_terms: includeInteractions, method: selectionMethod, criterion: selectionCriterion, alpha_enter: alphaValue, alpha_remove: 0.1 }); else if (validation) await createOlsValidationRun({ ...payload, method: validationMethod, folds: validationFolds, holdout_fraction: 0.2 }); else if (bestSubsets) await createBestSubsetsOlsRun({ ...payload, top_models_per_size: 1 }); else await createLinearOlsRun(payload);
      }
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석을 실행하지 못했습니다.");
      valuesRef.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  const title = normality ? "정규성 검정 설정" : logistic ? "로지스틱 회귀 설정" : poisson ? "Poisson 회귀 설정" : polynomial ? "다항회귀 분석 설정" : interaction ? "교호작용 회귀 분석 설정" : stepwise ? "단계선택 회귀 설정" : validation ? "회귀 모형 검증 설정" : bestSubsets ? "최적 부분집합 회귀 설정" : "선형회귀 분석 설정";
  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/analyses"><ArrowLeft aria-hidden="true" /> 분석 선택</Link>
    <section className="page-heading"><div><span className="eyebrow">STATISTICAL ANALYSIS</span><h1>{title}</h1><p>{normality ? "Jarque–Bera 검정으로 데이터의 정규성 가정을 점검합니다." : logistic ? "0/1 결과(Y)의 발생확률과 오즈비를 추정합니다." : poisson ? "불량·고장처럼 0 이상 정수로 기록된 건수(Y)의 발생률을 log-link Poisson 모형으로 추정합니다." : polynomial ? "연속형 결과(Y)의 곡선 관계를 2차 또는 3차 다항 OLS로 추정합니다." : interaction ? "연속형 결과(Y)에서 두 X의 결합 효과를 모든 2요인 교호작용 OLS로 추정합니다." : stepwise ? "후보 X에서 정보기준 또는 유의수준으로 항을 탐색합니다. 결과는 확인 실험 전의 후보 모형입니다." : validation ? "학습에 사용하지 않은 행으로 RMSE·MAE·예측 R²를 계산합니다. 시간 순서가 중요하면 홀드아웃을 사용하세요." : "연속형 결과(Y)와 하나 이상의 설명변수(X) 관계를 OLS로 추정합니다."}</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>분석 실행 정보</h2><p>분석 실행은 입력값과 엔진 버전을 고정해 보존합니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>유의수준 α</span><input type="number" step="0.001" min="0.001" max="0.5" value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label>{polynomial && <label className="field"><span>다항 차수</span><select value={degree} onChange={(event) => setDegree(Number(event.target.value) as 2 | 3)}><option value={2}>2차</option><option value={3}>3차</option></select><small>상호작용 항은 포함하지 않습니다.</small></label>}{stepwise && <><label className="field"><span>선택 방식</span><select value={selectionMethod} onChange={(event) => setSelectionMethod(event.target.value as "forward" | "backward" | "stepwise")}><option value="stepwise">단계선택 (진입·제거)</option><option value="forward">전진 선택</option><option value="backward">후진 제거</option></select></label><label className="field"><span>비교 기준</span><select value={selectionCriterion} onChange={(event) => setSelectionCriterion(event.target.value as "aicc" | "bic")}><option value="aicc">AICc</option><option value="bic">BIC</option></select></label><label className="field"><span>후보 항</span><span><input type="checkbox" aria-label="2요인 교호작용 후보 포함" checked={includeInteractions} onChange={(event) => setIncludeInteractions(event.target.checked)} /> 2요인 교호작용 후보 포함</span><small>교호작용이 선택되면 하위 주효과를 함께 유지합니다.</small></label></>}{!normality && <label className="field"><span>응답변수 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label>}</div></section>
      {validation && <section className="form-panel"><header><span className="step-index">01A</span><div><h2>검증 방법</h2><p>기본 k-fold는 행 순서대로 균등 분할합니다. 시간 순서가 있는 공정 데이터는 마지막 20%를 홀드아웃으로 검증하세요.</p></div></header><div className="inline-fields"><label className="field"><span>검증 방식</span><select value={validationMethod} onChange={(event) => setValidationMethod(event.target.value as "k_fold" | "holdout")}><option value="k_fold">k-fold 교차검증</option><option value="holdout">마지막 20% 홀드아웃</option></select></label>{validationMethod === "k_fold" && <label className="field"><span>분할 수 k</span><select value={validationFolds} onChange={(event) => setValidationFolds(Number(event.target.value))}><option value={3}>3</option><option value={5}>5</option><option value={10}>10</option></select></label>}</div></section>}
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>{normality ? "검정할 측정값" : "응답변수(Y)"}</h2><p>줄바꿈·쉼표·공백으로 구분한 숫자를 입력합니다. 결측값을 0으로 대체하지 않습니다.</p></div></header><label className="field"><span>{normality ? "측정값 *" : "응답값(Y) *"}</span><textarea ref={valuesRef} rows={8} value={values} onChange={(event) => setValues(event.target.value)} /><small>{parsed.filter(Number.isFinite).length}개 값 인식됨</small></label></section>
      {!normality && <section className="form-panel"><header><span className="step-index">03</span><div><h2>설명변수(X)</h2><p>각 X는 응답값과 같은 행 순서·개수로 입력합니다. {polynomial ? `차수 ${degree}에서는 최대 ${Math.floor(20 / degree)}개 X(확장 항 최대 20개)를 사용할 수 있습니다.` : includesTwoFactorInteractions ? "주효과와 모든 2요인 교호작용을 합쳐 최대 20항이며, 2~5개 X를 사용할 수 있습니다." : "엔진은 최대 20개 변수를 지원합니다."}</p></div></header>{predictorColumns.map((predictor, index) => <div className="form-panel" key={predictor.id}><header><h3>설명변수 {index + 1}</h3>{predictors.length > (interaction ? 2 : 1) && <Button type="button" variant="ghost" onClick={() => setPredictors((current) => current.filter((item) => item.id !== predictor.id))} icon={<Trash2 aria-hidden="true" />}>삭제</Button>}</header><div className="inline-fields"><label className="field"><span>설명변수 이름</span><input value={predictor.name} onChange={(event) => updatePredictor(predictor.id, "name", event.target.value)} required /></label></div><label className="field"><span>{predictor.name.trim() || `설명변수 ${index + 1}`} 값(X) *</span><textarea rows={8} value={predictor.values} onChange={(event) => updatePredictor(predictor.id, "values", event.target.value)} /><small>{predictor.parsed.filter(Number.isFinite).length}개 값 인식됨 · 응답값 {parsed.length}개 필요</small></label></div>)}<div className="form-actions">{predictors.length < maximumPredictors && <Button type="button" variant="secondary" onClick={addPredictor} icon={<Plus aria-hidden="true" />}>설명변수 추가</Button>}</div></section>}
      <aside className="method-note"><strong>해석 전 확인</strong><p>{normality ? "Jarque–Bera는 점근 카이제곱 근사를 사용합니다. 작은 표본에서는 결과를 단독 확정 근거로 사용하지 마세요." : polynomial ? "다항 항은 관측된 X 범위의 곡률을 근사합니다. 범위 밖 예측, 상호작용, 자동 변수선택은 제공하지 않으므로 잔차·공정 제약·확인 실험을 함께 검토하세요." : interaction ? "교호작용은 한 X의 효과가 다른 X 수준에 따라 달라질 때만 해석합니다. 주효과와 교호작용을 함께 검토하고, 조합별 관측 수·잔차·확인 실험을 확인하세요." : stepwise ? "자동 선택은 탐색을 돕지만 인과관계를 확정하지 않습니다. 선택 이력·공선성·영향 관측치·독립 검증을 확인하고 공정 제약을 반영한 확인 실험을 수행하세요." : logistic ? "로지스틱 회귀는 독립 관측과 이진 결과 코딩을 전제로 합니다. 분류 정확도만으로 운영 기준을 확정하지 마세요." : poisson ? "Poisson 회귀는 독립 관측과 조건부 평균·분산의 동등성을 가정합니다. 과산포 또는 영과다가 의심되면 이 결과만으로 공정 설정을 확정하지 말고 잔차·시간 의존성·대체 모형을 검토하세요." : "OLS는 독립성·선형성·등분산성과 잔차 검토가 필요합니다. 유의성만으로 운영 설정을 확정하지 말고 공정 제약과 확인 실험을 함께 검토하세요."}</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>{normality ? "정규성 검정 실행" : logistic ? "로지스틱 회귀 실행" : poisson ? "Poisson 회귀 실행" : polynomial ? "다항회귀 분석 실행" : interaction ? "교호작용 회귀 분석 실행" : stepwise ? "단계선택 회귀 실행" : validation ? "회귀 모형 검증 실행" : bestSubsets ? "최적 부분집합 비교 실행" : "선형회귀 분석 실행"}</Button></div>
    </form>
  </div>;
}

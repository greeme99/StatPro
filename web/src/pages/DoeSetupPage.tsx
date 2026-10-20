import { AlertTriangle, ArrowLeft, FlaskConical, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createDoeAnalysisRun } from "../api";
import { Button } from "../components/Button";

type FactorInput = { name: string; low: string; high: string };

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `doe-${timestamp}`;
}

export function DoeSetupPage() {
  const navigate = useNavigate();
  const responseRef = useRef<HTMLTextAreaElement>(null);
  const [runId, setRunId] = useState(defaultRunId);
  const [responseName, setResponseName] = useState("Strength");
  const [factors, setFactors] = useState<FactorInput[]>([
    { name: "A", low: "0", high: "1" },
    { name: "B", low: "10", high: "20" },
  ]);
  const [replicates, setReplicates] = useState(2);
  const [centerPoints, setCenterPoints] = useState(0);
  const [interactionOrder, setInteractionOrder] = useState(2);
  const [predictionLevels, setPredictionLevels] = useState(["0.75", "15"]);
  const [optimizationGoal, setOptimizationGoal] = useState<"maximize" | "minimize">("maximize");
  const [responses, setResponses] = useState("10\n14\n12\n20\n12\n16\n10\n22");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const parsedResponses = useMemo(
    () => responses.split(/[\s,;]+/).filter(Boolean).map(Number),
    [responses],
  );
  const expectedResponses = 2 ** factors.length * replicates + centerPoints;

  function updateFactor(index: number, key: keyof FactorInput, value: string) {
    setFactors((current) => current.map((factor, candidate) => candidate === index ? { ...factor, [key]: value } : factor));
  }

  function addFactor() {
    setFactors((current) => [...current, { name: `F${current.length + 1}`, low: "0", high: "1" }]);
    setPredictionLevels((current) => [...current, "0.5"]);
  }

  function removeFactor(index: number) {
    if (factors.length <= 2) return;
    const next = factors.filter((_, candidate) => candidate !== index);
    setFactors(next);
    setPredictionLevels((current) => current.filter((_, candidate) => candidate !== index));
    setInteractionOrder((order) => Math.min(order, next.length));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const normalized = factors.map((factor) => ({
      name: factor.name.trim(),
      low: Number(factor.low),
      high: Number(factor.high),
    }));
    if (normalized.some((factor) => !factor.name || !Number.isFinite(factor.low) || !Number.isFinite(factor.high) || factor.low >= factor.high)) {
      setError("모든 요인의 이름과 유한한 Low/High 수준을 확인하세요. Low는 High보다 작아야 합니다.");
      return;
    }
    if (new Set(normalized.map((factor) => factor.name)).size !== normalized.length) {
      setError("요인 이름은 중복될 수 없습니다.");
      return;
    }
    const predictionValues = predictionLevels.map(Number);
    if (predictionValues.some((value, index) => !Number.isFinite(value) || value < normalized[index].low || value > normalized[index].high)) {
      setError("예측 수준은 각 요인의 Low와 High 사이의 유한한 값이어야 합니다.");
      return;
    }
    const predictionPoint = Object.fromEntries(normalized.map((factor, index) => [factor.name, predictionValues[index]]));
    if (parsedResponses.length !== expectedResponses || parsedResponses.some((value) => !Number.isFinite(value))) {
      setError(`응답값 ${expectedResponses}개가 필요합니다. 현재 ${parsedResponses.filter(Number.isFinite).length}개가 인식되었습니다.`);
      responseRef.current?.focus();
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createDoeAnalysisRun({
        run_id: runId,
        factors: normalized,
        responses: parsedResponses,
        response_name: responseName.trim(),
        replicates,
        center_points: centerPoints,
        randomize: false,
        seed: 0,
        interaction_order: interactionOrder,
        prediction_points: [predictionPoint],
        optimization_goal: optimizationGoal,
      });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "DOE 분석을 실행하지 못했습니다.");
    } finally { setLoading(false); }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">DOE / TWO-LEVEL FACTORIAL</span><h1>완전요인 DOE 분석</h1><p>표준순서 응답으로 효과, coded coefficient, ANOVA와 잔차를 계산합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행과 응답</h2><p>불변 Analysis Run과 응답 열의 이름을 지정합니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>응답 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label></div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>요인과 수준</h2><p>2–12개 요인의 Low/High 수준을 입력합니다.</p></div></header><div className="factor-editor"><div className="factor-editor-head"><span>요인</span><span>Low</span><span>High</span><span className="sr-only">삭제</span></div>{factors.map((factor, index) => <div className="factor-editor-row" key={index}><label><span className="sr-only">요인 {index + 1} 이름</span><input value={factor.name} onChange={(event) => updateFactor(index, "name", event.target.value)} required /></label><label><span className="sr-only">{factor.name} Low</span><input type="number" step="any" value={factor.low} onChange={(event) => updateFactor(index, "low", event.target.value)} required /></label><label><span className="sr-only">{factor.name} High</span><input type="number" step="any" value={factor.high} onChange={(event) => updateFactor(index, "high", event.target.value)} required /></label><button className="icon-button" type="button" aria-label={`요인 ${factor.name} 삭제`} disabled={factors.length <= 2} onClick={() => removeFactor(index)}><Trash2 /></button></div>)}</div><Button type="button" disabled={factors.length >= 12} onClick={addFactor} icon={<Plus />}>요인 추가</Button></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>모델 범위</h2><p>반복, 중심점과 포함할 최대 교호작용 차수를 지정합니다.</p></div></header><div className="inline-fields"><label className="field"><span>반복 수</span><input type="number" min="1" value={replicates} onChange={(event) => setReplicates(Number(event.target.value))} required /></label><label className="field"><span>중심점 수</span><input type="number" min="0" value={centerPoints} onChange={(event) => setCenterPoints(Number(event.target.value))} required /></label><label className="field"><span>최대 교호작용 차수</span><select value={interactionOrder} onChange={(event) => setInteractionOrder(Number(event.target.value))}>{factors.map((_, index) => <option value={index + 1} key={index + 1}>{index + 1}</option>)}</select></label></div></section>
      <section className="form-panel"><header><span className="step-index">04</span><div><h2>예측과 최적화</h2><p>설계영역 내부의 한 조건을 예측하고 최대 또는 최소 꼭짓점을 탐색합니다.</p></div></header><div><div className="inline-fields">{factors.map((factor, index) => <label className="field" key={`${factor.name}-${index}`}><span>{factor.name || `요인 ${index + 1}`} 예측 수준</span><input type="number" step="any" value={predictionLevels[index]} onChange={(event) => setPredictionLevels((current) => current.map((value, candidate) => candidate === index ? event.target.value : value))} required /></label>)}</div><label className="field optimization-goal"><span>최적화 목표</span><select value={optimizationGoal} onChange={(event) => setOptimizationGoal(event.target.value as "maximize" | "minimize")}><option value="maximize">응답 최대화</option><option value="minimize">응답 최소화</option></select></label></div></section>
      <section className="form-panel"><header><span className="step-index">05</span><div><h2>표준순서 응답</h2><p>각 반복의 2ᵏ 표준순서 뒤에 중심점 응답을 입력합니다.</p></div></header><label className="field"><span>응답값 *</span><textarea ref={responseRef} rows={12} value={responses} onChange={(event) => setResponses(event.target.value)} aria-invalid={Boolean(error)} /><small>{expectedResponses}개 필요 · {parsedResponses.filter(Number.isFinite).length}개 유한값 인식</small></label></section>
      <aside className="method-note"><strong>계산 방법</strong><p>±1 coded least-squares 모델을 사용합니다. 반복점은 순수오차를 제공하며, 잔차의 독립성·등분산성·근사 정규성은 결과 플롯으로 검토해야 합니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<FlaskConical />}>DOE 분석 실행</Button></div>
    </form>
  </div>;
}

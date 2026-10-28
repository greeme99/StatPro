import { AlertTriangle, ArrowLeft, FlaskConical, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createDoeResponseOptimizerRun, type DoeResponseObjectivePayload } from "../api";
import { Button } from "../components/Button";

type FactorInput = { name: string; low: string; high: string };
type ObjectiveInput = {
  name: string;
  responses: string;
  goal: "maximize" | "minimize" | "target";
  lower: string;
  target: string;
  upper: string;
  weight: string;
  importance: string;
};

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `doe-opt-${timestamp}`;
}

function parseValues(value: string) {
  return value.split(/[\s,;]+/).filter(Boolean).map(Number);
}

export function DoeOptimizerPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [factors, setFactors] = useState<FactorInput[]>([
    { name: "A", low: "0", high: "1" },
    { name: "B", low: "0", high: "1" },
  ]);
  const [replicates, setReplicates] = useState(1);
  const [centerPoints, setCenterPoints] = useState(0);
  const [interactionOrder, setInteractionOrder] = useState(1);
  const [factorConstraints, setFactorConstraints] = useState("");
  const [objectives, setObjectives] = useState<ObjectiveInput[]>([
    { name: "Yield", responses: "0\n10\n0\n10", goal: "maximize", lower: "0", target: "10", upper: "", weight: "1", importance: "1" },
    { name: "Cost", responses: "0\n0\n10\n10", goal: "minimize", lower: "", target: "0", upper: "10", weight: "1", importance: "1" },
  ]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const expectedResponses = 2 ** factors.length * replicates + centerPoints;

  function updateFactor(index: number, key: keyof FactorInput, value: string) {
    setFactors((current) => current.map((factor, candidate) => candidate === index ? { ...factor, [key]: value } : factor));
  }

  function addFactor() {
    setFactors((current) => [...current, { name: `F${current.length + 1}`, low: "0", high: "1" }]);
  }

  function removeFactor(index: number) {
    if (factors.length <= 2) return;
    const next = factors.filter((_, candidate) => candidate !== index);
    setFactors(next);
    setInteractionOrder((order) => Math.min(order, next.length));
  }

  function updateObjective<K extends keyof ObjectiveInput>(index: number, key: K, value: ObjectiveInput[K]) {
    setObjectives((current) => current.map((objective, candidate) => candidate === index ? { ...objective, [key]: value } : objective));
  }

  function addObjective() {
    setObjectives((current) => [...current, { name: `Response ${current.length + 1}`, responses: "", goal: "target", lower: "0", target: "0.5", upper: "1", weight: "1", importance: "1" }]);
  }

  function removeObjective(index: number) {
    if (objectives.length <= 1) return;
    setObjectives((current) => current.filter((_, candidate) => candidate !== index));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const normalizedFactors = factors.map((factor) => ({ name: factor.name.trim(), low: Number(factor.low), high: Number(factor.high) }));
    if (normalizedFactors.some((factor) => !factor.name || !Number.isFinite(factor.low) || !Number.isFinite(factor.high) || factor.low >= factor.high)) {
      setError("모든 요인의 이름과 유한한 Low/High 수준을 확인하세요.");
      return;
    }
    if (new Set(normalizedFactors.map((factor) => factor.name)).size !== normalizedFactors.length) {
      setError("요인 이름은 중복될 수 없습니다.");
      return;
    }
    if (new Set(objectives.map((objective) => objective.name.trim())).size !== objectives.length || objectives.some((objective) => !objective.name.trim())) {
      setError("응답 이름은 비어 있거나 중복될 수 없습니다.");
      return;
    }
    const normalizedObjectives: DoeResponseObjectivePayload[] = [];
    const normalizedConstraints: Record<string, { lower: number; upper: number }> = {};
    for (const [index, line] of factorConstraints.split(/\r?\n/).map((value) => value.trim()).filter(Boolean).entries()) {
      const [name, lowerText, upperText, ...extra] = line.split(/[\s,;]+/);
      const lower = Number(lowerText);
      const upper = Number(upperText);
      const factor = normalizedFactors.find((candidate) => candidate.name === name);
      if (!factor || normalizedConstraints[name] || extra.length || !Number.isFinite(lower) || !Number.isFinite(upper) || lower < factor.low || upper > factor.high || lower > upper) {
        setError(`요인 제약 ${index + 1}행은 '요인 Lower Upper' 형식이며 설계 범위 안이어야 합니다.`);
        return;
      }
      normalizedConstraints[name] = { lower, upper };
    }
    for (const objective of objectives) {
      const responses = parseValues(objective.responses);
      const lower = objective.lower === "" ? undefined : Number(objective.lower);
      const target = Number(objective.target);
      const upper = objective.upper === "" ? undefined : Number(objective.upper);
      const weight = Number(objective.weight);
      const importance = Number(objective.importance);
      if (responses.length !== expectedResponses || responses.some((value) => !Number.isFinite(value))) {
        setError(`${objective.name} 응답값 ${expectedResponses}개가 필요합니다.`);
        return;
      }
      if (!Number.isFinite(target) || !Number.isFinite(weight) || !Number.isFinite(importance) || weight < 0.1 || weight > 10 || importance < 0.1 || importance > 10) {
        setError(`${objective.name}의 목표·가중치·중요도를 확인하세요. 가중치와 중요도는 0.1–10입니다.`);
        return;
      }
      if (objective.goal === "maximize" && (!Number.isFinite(lower) || Number(lower) >= target)) {
        setError(`${objective.name} 최대화는 Lower < Target이어야 합니다.`);
        return;
      }
      if (objective.goal === "minimize" && (!Number.isFinite(upper) || target >= Number(upper))) {
        setError(`${objective.name} 최소화는 Target < Upper여야 합니다.`);
        return;
      }
      if (objective.goal === "target" && (!Number.isFinite(lower) || !Number.isFinite(upper) || Number(lower) >= target || target >= Number(upper))) {
        setError(`${objective.name} 목표값은 Lower < Target < Upper여야 합니다.`);
        return;
      }
      normalizedObjectives.push({ name: objective.name.trim(), responses, goal: objective.goal, lower, target, upper, weight, importance });
    }
    setError("");
    setLoading(true);
    try {
      await createDoeResponseOptimizerRun({
        run_id: runId,
        factors: normalizedFactors,
        objectives: normalizedObjectives,
        replicates,
        center_points: centerPoints,
        randomize: false,
        seed: 0,
        interaction_order: interactionOrder,
        factor_constraints: normalizedConstraints,
      });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "DOE 응답 최적화를 실행하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">DOE / RESPONSE OPTIMIZER</span><h1>다중 응답 desirability 최적화</h1><p>같은 완전요인 설계의 여러 응답을 목표·최대·최소 기준으로 함께 최적화합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 설정</h2><p>불변 Run ID와 응답 배열의 공통 실행 수를 지정합니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>반복 수</span><input type="number" min="1" value={replicates} onChange={(event) => setReplicates(Number(event.target.value))} required /></label><label className="field"><span>중심점 수</span><input type="number" min="0" value={centerPoints} onChange={(event) => setCenterPoints(Number(event.target.value))} required /></label></div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>요인과 수준</h2><p>2–12개 정량 요인의 Low/High 수준과 선택적 탐색 제약을 입력합니다.</p></div></header><div><div className="factor-editor"><div className="factor-editor-head"><span>요인</span><span>Low</span><span>High</span><span className="sr-only">삭제</span></div>{factors.map((factor, index) => <div className="factor-editor-row" key={index}><label><span className="sr-only">요인 {index + 1} 이름</span><input value={factor.name} onChange={(event) => updateFactor(index, "name", event.target.value)} required /></label><label><span className="sr-only">{factor.name} Low</span><input type="number" step="any" value={factor.low} onChange={(event) => updateFactor(index, "low", event.target.value)} required /></label><label><span className="sr-only">{factor.name} High</span><input type="number" step="any" value={factor.high} onChange={(event) => updateFactor(index, "high", event.target.value)} required /></label><button className="icon-button" type="button" aria-label={`요인 ${factor.name} 삭제`} disabled={factors.length <= 2} onClick={() => removeFactor(index)}><Trash2 /></button></div>)}</div><Button type="button" disabled={factors.length >= 12} onClick={addFactor} icon={<Plus />}>요인 추가</Button><label className="field optimization-goal"><span>최대 교호작용 차수</span><select value={interactionOrder} onChange={(event) => setInteractionOrder(Number(event.target.value))}>{factors.map((_, index) => <option value={index + 1} key={index + 1}>{index + 1}</option>)}</select></label><label className="field"><span>요인 탐색 제약 (선택)</span><textarea aria-label="요인 탐색 제약 (선택)" rows={3} value={factorConstraints} onChange={(event) => setFactorConstraints(event.target.value)} placeholder={"A 0.2 0.8\nB 0.4 0.4"} /><small>한 줄에 요인명, Lower, Upper. Lower=Upper이면 해당 값에 고정합니다.</small></label></div></section>
      {objectives.map((objective, index) => <section className="form-panel" key={index}><header><span className="step-index">{String(index + 3).padStart(2, "0")}</span><div><h2>응답 {index + 1} · {objective.name || "이름 없음"}</h2><p>{expectedResponses}개 표준순서 응답과 desirability 기준을 입력합니다.</p></div></header><div><div className="inline-fields"><label className="field"><span>응답 이름</span><input value={objective.name} onChange={(event) => updateObjective(index, "name", event.target.value)} required /></label><label className="field"><span>목표</span><select value={objective.goal} onChange={(event) => updateObjective(index, "goal", event.target.value as ObjectiveInput["goal"])}><option value="maximize">최대화</option><option value="minimize">최소화</option><option value="target">목표값</option></select></label><label className="field"><span>가중치</span><input type="number" min="0.1" max="10" step="0.1" value={objective.weight} onChange={(event) => updateObjective(index, "weight", event.target.value)} required /></label><label className="field"><span>Lower</span><input type="number" step="any" value={objective.lower} onChange={(event) => updateObjective(index, "lower", event.target.value)} disabled={objective.goal === "minimize"} /></label><label className="field"><span>Target</span><input type="number" step="any" value={objective.target} onChange={(event) => updateObjective(index, "target", event.target.value)} required /></label><label className="field"><span>Upper</span><input type="number" step="any" value={objective.upper} onChange={(event) => updateObjective(index, "upper", event.target.value)} disabled={objective.goal === "maximize"} /></label><label className="field"><span>중요도</span><input type="number" min="0.1" max="10" step="0.1" value={objective.importance} onChange={(event) => updateObjective(index, "importance", event.target.value)} required /></label></div><label className="field"><span>{objective.name || `응답 ${index + 1}`} 표준순서 값 *</span><textarea rows={6} value={objective.responses} onChange={(event) => updateObjective(index, "responses", event.target.value)} required /><small>{expectedResponses}개 필요 · {parseValues(objective.responses).filter(Number.isFinite).length}개 유한값 인식</small></label><Button type="button" disabled={objectives.length <= 1} onClick={() => removeObjective(index)} icon={<Trash2 />}>응답 삭제</Button></div></section>)}
      <div className="page-actions"><Button type="button" disabled={objectives.length >= 10} onClick={addObjective} icon={<Plus />}>응답 추가</Button></div>
      <aside className="method-note"><strong>계산 방법</strong><p>각 응답에 같은 coded 모델을 적합하고 개별 desirability를 계산한 뒤 중요도 가중 기하평균을 최대화합니다. 결정론적 다중 시작 패턴 탐색은 설계영역 안에서 작동하지만 전역 최적을 보장하지 않습니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<FlaskConical />}>응답 최적화 실행</Button></div>
    </form>
  </div>;
}

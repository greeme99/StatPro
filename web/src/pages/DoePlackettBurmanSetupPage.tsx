import { AlertTriangle, ArrowLeft, FlaskConical, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createDoePlackettBurmanAnalysisRun, createDoePlackettBurmanRun } from "../api";
import { Button } from "../components/Button";

type FactorInput = { name: string; low: string; high: string };

const supportedRuns = [12, 20, 24, 28, 32, 36, 40, 44, 48] as const;

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `doe-pb-${timestamp}`;
}

export function DoePlackettBurmanSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [factors, setFactors] = useState<FactorInput[]>([
    { name: "A", low: "0", high: "1" },
    { name: "B", low: "0", high: "1" },
    { name: "C", low: "0", high: "1" },
    { name: "D", low: "0", high: "1" },
  ]);
  const [runs, setRuns] = useState<"auto" | number>("auto");
  const [replicates, setReplicates] = useState(1);
  const [centerPoints, setCenterPoints] = useState(0);
  const [randomize, setRandomize] = useState(true);
  const [seed, setSeed] = useState(0);
  const [analyzeResponses, setAnalyzeResponses] = useState(false);
  const [responseName, setResponseName] = useState("Response");
  const [responses, setResponses] = useState("");
  const [alpha, setAlpha] = useState(0.05);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const baseRuns = useMemo(
    () => runs === "auto" ? supportedRuns.find((candidate) => factors.length < candidate) ?? 48 : runs,
    [factors.length, runs],
  );
  const estimatedRuns = baseRuns * replicates + centerPoints;

  function updateFactor(index: number, key: keyof FactorInput, value: string) {
    setFactors((current) => current.map((item, candidate) => candidate === index ? { ...item, [key]: value } : item));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const normalizedFactors = factors.map((factor) => ({
      name: factor.name.trim(), low: Number(factor.low), high: Number(factor.high),
    }));
    if (normalizedFactors.some((factor) => !factor.name || !Number.isFinite(factor.low) || !Number.isFinite(factor.high) || factor.low >= factor.high)) {
      setError("모든 요인의 이름과 유한한 Low/High 수준을 확인하세요.");
      return;
    }
    if (new Set(normalizedFactors.map((factor) => factor.name)).size !== normalizedFactors.length) {
      setError("요인 이름은 중복될 수 없습니다.");
      return;
    }
    if (factors.length >= baseRuns) {
      setError(`선택한 ${baseRuns}회 설계에는 최대 ${baseRuns - 1}개 요인을 입력할 수 있습니다.`);
      return;
    }
    const responseValues = responses.split(/[\s,;]+/).filter(Boolean).map(Number);
    if (analyzeResponses && (responseValues.length !== estimatedRuns || responseValues.some((value) => !Number.isFinite(value)))) {
      setError(`응답은 실행순서대로 유한한 숫자 ${estimatedRuns}개를 입력하세요.`);
      return;
    }
    setError("");
    setLoading(true);
    try {
      const designPayload = {
        run_id: runId, factors: normalizedFactors,
        runs: runs === "auto" ? undefined : runs,
        replicates, center_points: centerPoints, randomize, seed,
      };
      if (analyzeResponses) {
        await createDoePlackettBurmanAnalysisRun({
          ...designPayload, responses: responseValues, response_name: responseName.trim(), alpha,
        });
      } else {
        await createDoePlackettBurmanRun(designPayload);
      }
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Plackett–Burman 설계를 생성하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">DOE / SCREENING</span><h1>Plackett–Burman 선별설계</h1><p>적은 실행으로 중요한 주효과 후보를 찾고 후속 실험 대상을 좁힙니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>재현 가능한 불변 Analysis Run ID를 지정합니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>요인과 수준</h2><p>2–47개 요인의 Low/High 수준을 입력합니다.</p></div></header><div><div className="factor-editor"><div className="factor-editor-head"><span>요인</span><span>Low</span><span>High</span><span className="sr-only">삭제</span></div>{factors.map((factor, index) => <div className="factor-editor-row" key={index}><label><span className="sr-only">요인 {index + 1} 이름</span><input value={factor.name} onChange={(event) => updateFactor(index, "name", event.target.value)} required /></label><label><span className="sr-only">{factor.name} Low</span><input type="number" step="any" value={factor.low} onChange={(event) => updateFactor(index, "low", event.target.value)} required /></label><label><span className="sr-only">{factor.name} High</span><input type="number" step="any" value={factor.high} onChange={(event) => updateFactor(index, "high", event.target.value)} required /></label><button className="icon-button" type="button" aria-label={`요인 ${factor.name} 삭제`} disabled={factors.length <= 2} onClick={() => setFactors((current) => current.filter((_, candidate) => candidate !== index))}><Trash2 /></button></div>)}</div><Button type="button" disabled={factors.length >= 47} onClick={() => setFactors((current) => [...current, { name: `F${current.length + 1}`, low: "0", high: "1" }])} icon={<Plus />}>요인 추가</Button></div></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>실행 계획</h2><p>설계 크기, 반복, 중심점과 무작위화를 지정합니다.</p></div></header><div><div className="inline-fields"><label className="field"><span>기본 실행 수</span><select aria-label="기본 실행 수" value={runs} onChange={(event) => setRuns(event.target.value === "auto" ? "auto" : Number(event.target.value))}><option value="auto">자동 선택</option>{supportedRuns.map((value) => <option value={value} key={value}>{value}회</option>)}</select></label><label className="field"><span>반복 수</span><input type="number" min="1" value={replicates} onChange={(event) => setReplicates(Number(event.target.value))} required /></label><label className="field"><span>중심점</span><input type="number" min="0" value={centerPoints} onChange={(event) => setCenterPoints(Number(event.target.value))} required /></label><label className="field"><span>무작위 seed</span><input type="number" value={seed} onChange={(event) => setSeed(Number(event.target.value))} required /></label></div><label className="check-field"><input type="checkbox" checked={randomize} onChange={(event) => setRandomize(event.target.checked)} /><span>실행순서 무작위화</span></label><p className="supporting-copy">기본 설계 {baseRuns}회 · 총 {estimatedRuns}회</p></div></section>
      <section className="form-panel"><header><span className="step-index">04</span><div><h2>응답 분석</h2><p>실험을 완료했다면 실행순서에 맞춘 응답으로 주효과를 선별합니다.</p></div></header><div><label className="check-field"><input type="checkbox" checked={analyzeResponses} onChange={(event) => setAnalyzeResponses(event.target.checked)} /><span>응답을 함께 분석</span></label>{analyzeResponses && <><div className="inline-fields"><label className="field"><span>응답 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label><label className="field"><span>유의수준 α</span><input type="number" min="0.001" max="0.5" step="0.001" value={alpha} onChange={(event) => setAlpha(Number(event.target.value))} required /></label></div><label className="field"><span>응답값 · {estimatedRuns}개</span><textarea value={responses} onChange={(event) => setResponses(event.target.value)} placeholder="실행순서대로 쉼표 또는 줄바꿈으로 구분" required /></label></>}</div></section>
      <aside className="method-note"><strong>선별설계 해석</strong><p>해상도 III에서는 주효과가 2요인 교호작용과 섞일 수 있습니다. 큰 효과 후보를 고른 뒤 요인설계 또는 반응표면 실험으로 확인하세요.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<FlaskConical />}>{analyzeResponses ? "응답 분석 실행" : "선별설계 생성"}</Button></div>
    </form>
  </div>;
}

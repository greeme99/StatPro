import { AlertTriangle, ArrowLeft, FlaskConical, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createDoeCentralCompositeAnalysisRun, createDoeCentralCompositeRun } from "../api";
import { Button } from "../components/Button";

type FactorInput = { name: string; low: string; high: string };

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `doe-ccd-${timestamp}`;
}

export function DoeCentralCompositeSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [factors, setFactors] = useState<FactorInput[]>([
    { name: "A", low: "0", high: "10" },
    { name: "B", low: "0", high: "20" },
  ]);
  const [designType, setDesignType] = useState<"rotatable" | "face_centered">("rotatable");
  const [centerPoints, setCenterPoints] = useState(5);
  const [replicates, setReplicates] = useState(1);
  const [randomize, setRandomize] = useState(true);
  const [seed, setSeed] = useState(0);
  const [analyzeResponses, setAnalyzeResponses] = useState(false);
  const [responseName, setResponseName] = useState("Response");
  const [responses, setResponses] = useState("");
  const [alpha, setAlpha] = useState(0.05);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const estimatedRuns = useMemo(
    () => (2 ** factors.length + 2 * factors.length) * replicates + centerPoints,
    [factors.length, replicates, centerPoints],
  );

  function updateFactor(index: number, key: keyof FactorInput, value: string) {
    setFactors((current) => current.map((factor, candidate) => candidate === index ? { ...factor, [key]: value } : factor));
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
    const normalizedResponses = responses.split(/[\s,;]+/).filter(Boolean).map(Number);
    if (analyzeResponses && (!responseName.trim() || normalizedResponses.length !== estimatedRuns || normalizedResponses.some((value) => !Number.isFinite(value)))) {
      setError(`실행순서 기준 유한 응답 ${estimatedRuns}개를 입력하세요.`);
      return;
    }
    setError("");
    setLoading(true);
    try {
      const payload = {
        run_id: runId,
        factors: normalizedFactors,
        design_type: designType,
        center_points: centerPoints,
        replicates,
        randomize,
        seed,
      };
      if (analyzeResponses) {
        await createDoeCentralCompositeAnalysisRun({ ...payload, responses: normalizedResponses, response_name: responseName.trim(), alpha });
      } else {
        await createDoeCentralCompositeRun(payload);
      }
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "중앙합성설계를 처리하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">DOE / RESPONSE SURFACE</span><h1>중앙합성설계</h1><p>factorial·axial·center point로 곡률을 추정하고 완전 2차 반응표면 모형을 적합합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>재현 가능한 불변 Analysis Run ID입니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>정량 요인과 factorial 수준</h2><p>2–6개 요인의 coded −1/+1에 대응하는 Low/High를 입력합니다.</p></div></header><div><div className="factor-editor"><div className="factor-editor-head"><span>요인</span><span>Low</span><span>High</span><span className="sr-only">삭제</span></div>{factors.map((factor, index) => <div className="factor-editor-row" key={index}><label><span className="sr-only">요인 {index + 1} 이름</span><input value={factor.name} onChange={(event) => updateFactor(index, "name", event.target.value)} required /></label><label><span className="sr-only">{factor.name} Low</span><input type="number" step="any" value={factor.low} onChange={(event) => updateFactor(index, "low", event.target.value)} required /></label><label><span className="sr-only">{factor.name} High</span><input type="number" step="any" value={factor.high} onChange={(event) => updateFactor(index, "high", event.target.value)} required /></label><button className="icon-button" type="button" aria-label={`요인 ${factor.name} 삭제`} disabled={factors.length <= 2} onClick={() => setFactors((current) => current.filter((_, candidate) => candidate !== index))}><Trash2 /></button></div>)}</div><Button type="button" disabled={factors.length >= 6} onClick={() => setFactors((current) => [...current, { name: `F${current.length + 1}`, low: "0", high: "1" }])} icon={<Plus />}>요인 추가</Button></div></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>설계 속성</h2><p>rotatable은 axial point가 범위 밖에 놓일 수 있고, face-centered는 Low/High 안에 머뭅니다.</p></div></header><div className="form-stack"><div className="inline-fields"><label className="field"><span>CCD 유형</span><select value={designType} onChange={(event) => setDesignType(event.target.value as "rotatable" | "face_centered")}><option value="rotatable">Rotatable circumscribed</option><option value="face_centered">Face-centered</option></select></label><label className="field"><span>중심점 수</span><input type="number" min="1" value={centerPoints} onChange={(event) => setCenterPoints(Number(event.target.value))} required /></label><label className="field"><span>기본점 반복</span><input type="number" min="1" value={replicates} onChange={(event) => setReplicates(Number(event.target.value))} required /></label><label className="field"><span>무작위 seed</span><input type="number" value={seed} onChange={(event) => setSeed(Number(event.target.value))} required /></label></div><label className="check-field"><input type="checkbox" checked={randomize} onChange={(event) => setRandomize(event.target.checked)} /><span>실행순서 무작위화</span></label><p className="supporting-copy">예상 실행 수: {estimatedRuns}회</p></div></section>
      <section className="form-panel"><header><span className="step-index">04</span><div><h2>2차 모형 분석</h2><p>선택하면 실행순서 응답에 선형·2요인 교호작용·제곱항을 적합합니다.</p></div></header><div><label className="check-field"><input type="checkbox" checked={analyzeResponses} onChange={(event) => setAnalyzeResponses(event.target.checked)} /><span>응답을 함께 분석</span></label>{analyzeResponses && <div className="form-stack"><div className="inline-fields"><label className="field"><span>응답 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label><label className="field"><span>유의수준 α</span><input type="number" min="0.001" max="0.5" step="0.001" value={alpha} onChange={(event) => setAlpha(Number(event.target.value))} required /></label></div><label className="field"><span>실행순서 응답 ({estimatedRuns}개)</span><textarea rows={7} value={responses} onChange={(event) => setResponses(event.target.value)} placeholder="공백, 쉼표 또는 줄바꿈으로 구분" required /></label></div>}</div></section>
      <aside className="method-note"><strong>실행 전 안전 확인</strong><p>Rotatable axial point는 입력한 Low/High보다 바깥에 놓일 수 있습니다. 장비·재료·공정의 안전 범위를 먼저 확인하세요.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<FlaskConical />}>{analyzeResponses ? "2차 모형 분석" : "중앙합성설계 생성"}</Button></div>
    </form>
  </div>;
}

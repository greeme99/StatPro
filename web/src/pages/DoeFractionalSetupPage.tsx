import { AlertTriangle, ArrowLeft, FlaskConical, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createDoeAutomaticFractionalFactorialAnalysisRun, createDoeAutomaticFractionalFactorialRun, createDoeFractionalFactorialAnalysisRun, createDoeFractionalFactorialRun } from "../api";
import { Button } from "../components/Button";

type FactorInput = { name: string; low: string; high: string };
type GeneratorInput = { factor: string; terms: string };

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `doe-frac-${timestamp}`;
}

export function DoeFractionalSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [factors, setFactors] = useState<FactorInput[]>([
    { name: "A", low: "0", high: "1" },
    { name: "B", low: "0", high: "1" },
    { name: "C", low: "0", high: "1" },
    { name: "D", low: "0", high: "1" },
  ]);
  const [generators, setGenerators] = useState<GeneratorInput[]>([
    { factor: "D", terms: "A B C" },
  ]);
  const [generatorMode, setGeneratorMode] = useState<"automatic" | "manual">("manual");
  const [automaticRuns, setAutomaticRuns] = useState(8);
  const [minimumResolution, setMinimumResolution] = useState(3);
  const [replicates, setReplicates] = useState(1);
  const [foldover, setFoldover] = useState(false);
  const [randomize, setRandomize] = useState(true);
  const [seed, setSeed] = useState(0);
  const [analyzeResponses, setAnalyzeResponses] = useState(false);
  const [responseName, setResponseName] = useState("Response");
  const [responses, setResponses] = useState("");
  const [alpha, setAlpha] = useState(0.05);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const automaticRunOptions = useMemo(
    () => Array.from({ length: Math.max(factors.length - 2, 0) }, (_, index) => 2 ** (index + 2)),
    [factors.length],
  );
  const resolvedAutomaticRuns = Math.min(automaticRuns, automaticRunOptions.at(-1) ?? 4);
  const effectiveFoldover = generatorMode === "automatic" ? false : foldover;
  const estimatedRuns = useMemo(
    () => (generatorMode === "automatic" ? resolvedAutomaticRuns : 2 ** Math.max(factors.length - generators.length, 0)) * replicates * (effectiveFoldover ? 2 : 1),
    [generatorMode, resolvedAutomaticRuns, factors.length, generators.length, replicates, effectiveFoldover],
  );

  function updateFactor(index: number, key: keyof FactorInput, value: string) {
    setFactors((current) => current.map((item, candidate) => candidate === index ? { ...item, [key]: value } : item));
  }

  function updateGenerator(index: number, key: keyof GeneratorInput, value: string) {
    setGenerators((current) => current.map((item, candidate) => candidate === index ? { ...item, [key]: value } : item));
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
    const names = normalizedFactors.map((factor) => factor.name);
    if (new Set(names).size !== names.length) {
      setError("요인 이름은 중복될 수 없습니다.");
      return;
    }
    const normalizedGenerators = generators.map((generator) => ({
      factor: generator.factor.trim(),
      terms: generator.terms.split(/[\s,*]+/).filter(Boolean),
    }));
    if (generatorMode === "manual") {
      const generatedNames = normalizedGenerators.map((generator) => generator.factor);
      const baseNames = new Set(names.filter((name) => !generatedNames.includes(name)));
      if (!normalizedGenerators.length || new Set(generatedNames).size !== generatedNames.length) {
        setError("생성 요인은 한 개 이상이어야 하며 중복될 수 없습니다.");
        return;
      }
      if (normalizedGenerators.some((generator) => !names.includes(generator.factor) || generator.terms.length < 2 || new Set(generator.terms).size !== generator.terms.length || generator.terms.some((term) => !baseNames.has(term)))) {
        setError("생성식은 대상 요인과 서로 다른 두 개 이상의 기본 요인으로 작성하세요. 예: D = A B C");
        return;
      }
    }
    const normalizedResponses = responses.split(/[\s,;]+/).filter(Boolean).map(Number);
    if (analyzeResponses && (!responseName.trim() || normalizedResponses.length !== estimatedRuns || normalizedResponses.some((value) => !Number.isFinite(value)))) {
      setError(`응답 이름과 실행순서 기준 유한 응답 ${estimatedRuns}개를 입력하세요.`);
      return;
    }
    setError("");
    setLoading(true);
    try {
      const commonPayload = {
        run_id: runId,
        factors: normalizedFactors,
        replicates,
        foldover: effectiveFoldover,
        randomize,
        seed,
      };
      if (generatorMode === "automatic") {
        const automaticPayload = {
          ...commonPayload,
          runs: resolvedAutomaticRuns,
          minimum_resolution: minimumResolution,
        };
        if (analyzeResponses) {
          await createDoeAutomaticFractionalFactorialAnalysisRun({
            ...automaticPayload,
            responses: normalizedResponses,
            response_name: responseName.trim(),
            alpha,
          });
        } else {
          await createDoeAutomaticFractionalFactorialRun(automaticPayload);
        }
      } else {
        const manualPayload = { ...commonPayload, generators: normalizedGenerators };
        if (analyzeResponses) {
          await createDoeFractionalFactorialAnalysisRun({
            ...manualPayload,
            responses: normalizedResponses,
            response_name: responseName.trim(),
            alpha,
          });
        } else {
          await createDoeFractionalFactorialRun(manualPayload);
        }
      }
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "일부요인배치를 생성하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">DOE / REGULAR FRACTION</span><h1>2수준 일부요인배치</h1><p>정규 2ᵏ⁻ᵖ 설계와 full foldover를 만들고, 실행순서 응답의 주효과를 별칭 한계와 함께 분석합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>재현 가능한 불변 Analysis Run ID를 지정합니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>요인과 수준</h2><p>3–12개 요인의 Low/High 수준을 입력합니다.</p></div></header><div><div className="factor-editor"><div className="factor-editor-head"><span>요인</span><span>Low</span><span>High</span><span className="sr-only">삭제</span></div>{factors.map((factor, index) => <div className="factor-editor-row" key={index}><label><span className="sr-only">요인 {index + 1} 이름</span><input value={factor.name} onChange={(event) => updateFactor(index, "name", event.target.value)} required /></label><label><span className="sr-only">{factor.name} Low</span><input type="number" step="any" value={factor.low} onChange={(event) => updateFactor(index, "low", event.target.value)} required /></label><label><span className="sr-only">{factor.name} High</span><input type="number" step="any" value={factor.high} onChange={(event) => updateFactor(index, "high", event.target.value)} required /></label><button className="icon-button" type="button" aria-label={`요인 ${factor.name} 삭제`} disabled={factors.length <= 3} onClick={() => setFactors((current) => current.filter((_, candidate) => candidate !== index))}><Trash2 /></button></div>)}</div><Button type="button" disabled={factors.length >= 12} onClick={() => setFactors((current) => [...current, { name: `F${current.length + 1}`, low: "0", high: "1" }])} icon={<Plus />}>요인 추가</Button></div></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>생성자 선택</h2><p>실행 수와 최소 해상도로 자동 선택하거나 생성식을 직접 지정합니다.</p></div></header><div className="form-stack"><div className="choice-grid" role="radiogroup" aria-label="생성자 선택 방식"><label className="check-field"><input type="radio" name="generator-mode" checked={generatorMode === "automatic"} onChange={() => setGeneratorMode("automatic")} /><span>자동 선택 · 최소 이상률</span></label><label className="check-field"><input type="radio" name="generator-mode" checked={generatorMode === "manual"} onChange={() => setGeneratorMode("manual")} /><span>생성식 직접 지정</span></label></div>{generatorMode === "automatic" ? <><div className="inline-fields"><label className="field"><span>기본 실행 수</span><select value={resolvedAutomaticRuns} onChange={(event) => setAutomaticRuns(Number(event.target.value))}>{automaticRunOptions.map((runs) => <option key={runs} value={runs}>{runs}회</option>)}</select></label><label className="field"><span>최소 해상도</span><input type="number" min="3" max={factors.length} value={minimumResolution} onChange={(event) => setMinimumResolution(Number(event.target.value))} required /></label></div><p className="supporting-copy">선택한 실행 수에서 A3, A4, … 단어 수를 사전식으로 최소화합니다. 동률이면 결정론적 기본요인 순서를 사용합니다.</p></> : <>{generators.map((generator, index) => <div className="inline-fields" key={index}><label className="field"><span>생성 요인</span><input aria-label={`생성 요인 ${index + 1}`} value={generator.factor} onChange={(event) => updateGenerator(index, "factor", event.target.value)} required /></label><label className="field"><span>기본 요인 곱</span><input aria-label={`생성식 ${index + 1}`} value={generator.terms} onChange={(event) => updateGenerator(index, "terms", event.target.value)} placeholder="A B C" required /></label><button className="icon-button" type="button" aria-label={`생성식 ${index + 1} 삭제`} disabled={generators.length <= 1} onClick={() => setGenerators((current) => current.filter((_, candidate) => candidate !== index))}><Trash2 /></button></div>)}<Button type="button" disabled={generators.length >= 8} onClick={() => setGenerators((current) => [...current, { factor: "", terms: "" }])} icon={<Plus />}>생성식 추가</Button></>}</div></section>
      <section className="form-panel"><header><span className="step-index">04</span><div><h2>실행 계획</h2><p>반복, full foldover, 무작위화와 재현 seed를 지정합니다.</p></div></header><div><div className="inline-fields"><label className="field"><span>반복 수</span><input type="number" min="1" value={replicates} onChange={(event) => setReplicates(Number(event.target.value))} required /></label><label className="field"><span>무작위 seed</span><input type="number" value={seed} onChange={(event) => setSeed(Number(event.target.value))} required /></label></div><label className="check-field"><input type="checkbox" checked={effectiveFoldover} disabled={generatorMode === "automatic"} onChange={(event) => setFoldover(event.target.checked)} /><span>해상도 III full mirror-image foldover 추가</span></label>{generatorMode === "automatic" ? <p className="supporting-copy">자동 선택 결과가 해상도 III인지 확인한 뒤, 선택된 생성식을 수동 모드에 입력하면 full foldover를 추가할 수 있습니다.</p> : null}<label className="check-field"><input type="checkbox" checked={randomize} onChange={(event) => setRandomize(event.target.checked)} /><span>실행순서 무작위화</span></label><p className="supporting-copy">예상 실행 수: {estimatedRuns}회</p></div></section>
      <section className="form-panel"><header><span className="step-index">05</span><div><h2>응답 분석</h2><p>선택하면 설계 실행순서와 일치하는 응답으로 주효과 대표항을 추정합니다.</p></div></header><div><label className="check-field"><input type="checkbox" checked={analyzeResponses} onChange={(event) => setAnalyzeResponses(event.target.checked)} /><span>응답을 함께 분석</span></label>{analyzeResponses && <div className="form-stack"><div className="inline-fields"><label className="field"><span>응답 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label><label className="field"><span>유의수준 α</span><input type="number" min="0.001" max="0.5" step="0.001" value={alpha} onChange={(event) => setAlpha(Number(event.target.value))} required /></label></div><label className="field"><span>실행순서 응답 ({estimatedRuns}개)</span><textarea rows={6} value={responses} onChange={(event) => setResponses(event.target.value)} placeholder="공백, 쉼표 또는 줄바꿈으로 구분" required /></label></div>}</div></section>
      <aside className="method-note"><strong>별칭 해석</strong><p>해상도 III은 주효과와 2요인 교호작용이, 해상도 IV는 2요인 교호작용끼리 별칭될 수 있습니다. 중요한 효과는 추가 실험으로 확인하세요.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<FlaskConical />}>{analyzeResponses ? "일부요인 응답 분석" : "일부요인배치 생성"}</Button></div>
    </form>
  </div>;
}

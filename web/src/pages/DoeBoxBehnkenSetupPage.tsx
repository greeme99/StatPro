import { AlertTriangle, ArrowLeft, FlaskConical, Plus, Trash2 } from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createDoeBoxBehnkenAnalysisRun, createDoeBoxBehnkenRun, createDoeBoxBehnkenSurfaceRun } from "../api";
import { Button } from "../components/Button";

type FactorInput = { name: string; low: string; high: string };

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `doe-bbd-${timestamp}`;
}

export function DoeBoxBehnkenSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [factors, setFactors] = useState<FactorInput[]>([
    { name: "A", low: "0", high: "10" },
    { name: "B", low: "0", high: "20" },
    { name: "C", low: "0", high: "30" },
  ]);
  const [centerPoints, setCenterPoints] = useState("");
  const [replicates, setReplicates] = useState(1);
  const [randomize, setRandomize] = useState(true);
  const [seed, setSeed] = useState(0);
  const [analyzeResponses, setAnalyzeResponses] = useState(false);
  const [responseName, setResponseName] = useState("Response");
  const [responses, setResponses] = useState("");
  const [alpha, setAlpha] = useState(0.05);
  const [exploreSurface, setExploreSurface] = useState(false);
  const [plotFactorX, setPlotFactorX] = useState(0);
  const [plotFactorY, setPlotFactorY] = useState(1);
  const [gridSize, setGridSize] = useState(21);
  const [contourLevels, setContourLevels] = useState(7);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const recommendedCenters = factors.length === 5 ? 6 : 3;
  const resolvedCenters = centerPoints === "" ? recommendedCenters : Number(centerPoints);
  const estimatedRuns = useMemo(
    () => 4 * factors.length * (factors.length - 1) / 2 * replicates + resolvedCenters,
    [factors.length, replicates, resolvedCenters],
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
    if (!Number.isInteger(replicates) || replicates < 1 || !Number.isInteger(resolvedCenters) || resolvedCenters < 1 || !Number.isInteger(seed)) {
      setError("반복·중심점은 양의 정수, seed는 정수로 입력하세요.");
      return;
    }
    const normalizedResponses = responses.split(/[\s,;]+/).filter(Boolean).map(Number);
    if (analyzeResponses && (!responseName.trim() || normalizedResponses.length !== estimatedRuns || normalizedResponses.some((value) => !Number.isFinite(value)))) {
      setError(`실행순서 기준 유한 응답 ${estimatedRuns}개를 입력하세요.`);
      return;
    }
    if (analyzeResponses && exploreSurface && (plotFactorX === plotFactorY || gridSize < 5 || gridSize > 51 || gridSize % 2 === 0 || contourLevels < 1 || contourLevels > 12)) {
      setError("표면 축은 서로 다른 두 요인을 선택하고, 격자는 5–51 사이 홀수, 등고선은 1–12개로 입력하세요.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const payload = {
        run_id: runId,
        factors: normalizedFactors,
        ...(centerPoints === "" ? {} : { center_points: resolvedCenters }),
        replicates,
        randomize,
        seed,
      };
      if (analyzeResponses && exploreSurface) {
        await createDoeBoxBehnkenSurfaceRun({
          ...payload,
          responses: normalizedResponses,
          response_name: responseName.trim(),
          alpha,
          plot_factors: [normalizedFactors[plotFactorX].name, normalizedFactors[plotFactorY].name],
          hold_values: {},
          grid_size: gridSize,
          contour_levels: contourLevels,
        });
      } else if (analyzeResponses) {
        await createDoeBoxBehnkenAnalysisRun({ ...payload, responses: normalizedResponses, response_name: responseName.trim(), alpha });
      } else {
        await createDoeBoxBehnkenRun(payload);
      }
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Box–Behnken 설계를 생성하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">DOE / RESPONSE SURFACE</span><h1>Box–Behnken 설계</h1><p>세 수준의 edge-midpoint와 center point로 완전 2차 반응표면 모형을 위한 실험표를 만듭니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>재현 가능한 불변 Analysis Run ID입니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>정량 요인과 수준</h2><p>3–5개 요인의 coded −1/0/+1에 대응할 Low·midpoint·High를 정의합니다.</p></div></header><div><div className="factor-editor"><div className="factor-editor-head"><span>요인</span><span>Low</span><span>High</span><span className="sr-only">삭제</span></div>{factors.map((factor, index) => <div className="factor-editor-row" key={index}><label><span className="sr-only">요인 {index + 1} 이름</span><input value={factor.name} onChange={(event) => updateFactor(index, "name", event.target.value)} required /></label><label><span className="sr-only">{factor.name} Low</span><input type="number" step="any" value={factor.low} onChange={(event) => updateFactor(index, "low", event.target.value)} required /></label><label><span className="sr-only">{factor.name} High</span><input type="number" step="any" value={factor.high} onChange={(event) => updateFactor(index, "high", event.target.value)} required /></label><button className="icon-button" type="button" aria-label={`요인 ${factor.name} 삭제`} disabled={factors.length <= 3} onClick={() => setFactors((current) => current.filter((_, candidate) => candidate !== index))}><Trash2 /></button></div>)}</div><Button type="button" disabled={factors.length >= 5} onClick={() => setFactors((current) => [...current, { name: `F${current.length + 1}`, low: "0", high: "1" }])} icon={<Plus />}>요인 추가</Button></div></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>설계 속성</h2><p>공개 표준 실행 수와 재현 가능한 무작위 순서를 설정합니다.</p></div></header><div className="form-stack"><div className="inline-fields"><label className="field"><span>중심점 수</span><input type="number" min="1" value={centerPoints} placeholder={`자동 ${recommendedCenters}`} onChange={(event) => setCenterPoints(event.target.value)} /></label><label className="field"><span>Edge block 반복</span><input type="number" min="1" value={replicates} onChange={(event) => setReplicates(Number(event.target.value))} required /></label><label className="field"><span>무작위 seed</span><input type="number" value={seed} onChange={(event) => setSeed(Number(event.target.value))} required /></label></div><label className="check-field"><input type="checkbox" checked={randomize} onChange={(event) => setRandomize(event.target.checked)} /><span>실행순서 무작위화</span></label><p className="supporting-copy">예상 실행 수: {estimatedRuns}회 · 중심점 {resolvedCenters}회</p></div></section>
      <section className="form-panel"><header><span className="step-index">04</span><div><h2>2차 모형 분석</h2><p>선택하면 실행순서 응답에 선형·2요인 교호작용·제곱항을 적합합니다.</p></div></header><div><label className="check-field"><input type="checkbox" checked={analyzeResponses} onChange={(event) => setAnalyzeResponses(event.target.checked)} /><span>응답을 함께 분석</span></label>{analyzeResponses && <div className="form-stack"><div className="inline-fields"><label className="field"><span>응답 이름</span><input value={responseName} onChange={(event) => setResponseName(event.target.value)} required /></label><label className="field"><span>유의수준 α</span><input type="number" min="0.001" max="0.5" step="0.001" value={alpha} onChange={(event) => setAlpha(Number(event.target.value))} required /></label></div><label className="field"><span>실행순서 응답 ({estimatedRuns}개)</span><textarea rows={7} value={responses} onChange={(event) => setResponses(event.target.value)} placeholder="공백, 쉼표 또는 줄바꿈으로 구분" required /></label><label className="check-field"><input type="checkbox" checked={exploreSurface} onChange={(event) => setExploreSurface(event.target.checked)} /><span>정상점과 2요인 응답표면 격자 탐색</span></label>{exploreSurface && <div className="inline-fields"><label className="field"><span>가로축 요인</span><select value={plotFactorX} onChange={(event) => setPlotFactorX(Number(event.target.value))}>{factors.map((factor, index) => <option value={index} key={index}>{factor.name || `요인 ${index + 1}`}</option>)}</select></label><label className="field"><span>세로축 요인</span><select value={plotFactorY} onChange={(event) => setPlotFactorY(Number(event.target.value))}>{factors.map((factor, index) => <option value={index} key={index}>{factor.name || `요인 ${index + 1}`}</option>)}</select></label><label className="field"><span>격자 크기</span><input type="number" min="5" max="51" step="2" value={gridSize} onChange={(event) => setGridSize(Number(event.target.value))} required /></label><label className="field"><span>등고선 수준 수</span><input type="number" min="1" max="12" value={contourLevels} onChange={(event) => setContourLevels(Number(event.target.value))} required /></label></div>}</div>}</div></section>
      <aside className="method-note"><strong>설계영역과 안전 확인</strong><p>모든 요인이 동시에 극단에 놓이는 cube corner는 포함하지 않지만, 생성된 각 공정 설정의 안전성과 실행 가능성은 별도로 확인해야 합니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<FlaskConical />}>{analyzeResponses ? (exploreSurface ? "응답표면 탐색" : "2차 모형 분석") : "Box–Behnken 설계 생성"}</Button></div>
    </form>
  </div>;
}

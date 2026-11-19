import { Play } from "lucide-react";
import { useState, type FormEvent } from "react";
import { createTwoSampleProportionRun } from "../api";
import { Button } from "../components/Button";

type Result = {
  proportion_a: number; proportion_b: number; difference: number; p_value: number;
  confidence_interval_lower: number; confidence_interval_upper: number; significant: boolean;
};

export function TwoSampleProportionPage() {
  const [runId, setRunId] = useState(`two-prop-${Date.now()}`);
  const [defectsA, setDefectsA] = useState("20"); const [opportunitiesA, setOpportunitiesA] = useState("100");
  const [defectsB, setDefectsB] = useState("5"); const [opportunitiesB, setOpportunitiesB] = useState("100");
  const [alpha, setAlpha] = useState("0.05"); const [result, setResult] = useState<Result | null>(null); const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    const input = { defects_a: Number(defectsA), opportunities_a: Number(opportunitiesA), defects_b: Number(defectsB), opportunities_b: Number(opportunitiesB), alpha: Number(alpha) };
    if (Object.values(input).some((value) => !Number.isFinite(value)) || !Number.isInteger(input.defects_a) || !Number.isInteger(input.defects_b) || !Number.isInteger(input.opportunities_a) || !Number.isInteger(input.opportunities_b) || input.defects_a < 0 || input.defects_b < 0 || input.opportunities_a <= 0 || input.opportunities_b <= 0 || input.defects_a > input.opportunities_a || input.defects_b > input.opportunities_b) { setError("두 집단의 불량 수와 검사 수를 확인하세요."); return; }
    try { const run = await createTwoSampleProportionRun({ run_id: runId, ...input }); setResult(run.result.diagnostics as Result); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "분석을 실행하지 못했습니다."); }
  }
  return <div className="page form-page"><section className="page-heading"><span className="eyebrow">PROPORTION TEST</span><h1>두 비율 비교</h1><p>두 생산라인 또는 개선 전후의 불량률 차이를 검증합니다.</p></section>{error && <p role="alert">{error}</p>}<form className="analysis-form" onSubmit={submit}><section className="form-panel"><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} /></label><label className="field"><span>집단 A 불량 수</span><input value={defectsA} onChange={(event) => setDefectsA(event.target.value)} /></label><label className="field"><span>집단 A 검사 수</span><input value={opportunitiesA} onChange={(event) => setOpportunitiesA(event.target.value)} /></label><label className="field"><span>집단 B 불량 수</span><input value={defectsB} onChange={(event) => setDefectsB(event.target.value)} /></label><label className="field"><span>집단 B 검사 수</span><input value={opportunitiesB} onChange={(event) => setOpportunitiesB(event.target.value)} /></label><label className="field"><span>유의수준 α</span><input value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label></div></section><div className="form-actions"><Button type="submit" variant="primary" icon={<Play />}>두 비율 검정 실행</Button></div></form>{result && <section className="metric-grid result-metrics"><article className="metric-card"><span>A 불량률</span><strong>{(result.proportion_a * 100).toFixed(2)}%</strong></article><article className="metric-card"><span>B 불량률</span><strong>{(result.proportion_b * 100).toFixed(2)}%</strong></article><article className="metric-card"><span>차이 및 95% CI</span><strong>{(result.difference * 100).toFixed(2)}%</strong><small>{(result.confidence_interval_lower * 100).toFixed(2)}% ~ {(result.confidence_interval_upper * 100).toFixed(2)}%, p={result.p_value.toFixed(4)}</small></article></section>}</div>;
}

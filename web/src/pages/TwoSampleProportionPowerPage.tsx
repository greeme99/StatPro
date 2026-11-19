import { Play } from "lucide-react";
import { useState, type FormEvent } from "react";
import { createTwoSampleProportionPowerRun } from "../api";
import { Button } from "../components/Button";

type Plan = { sample_size_per_group: number; total_sample_size: number; absolute_difference: number };

export function TwoSampleProportionPowerPage() {
  const [runId, setRunId] = useState(`proportion-power-${Date.now()}`);
  const [proportionA, setProportionA] = useState("0.20"); const [proportionB, setProportionB] = useState("0.05");
  const [alpha, setAlpha] = useState("0.05"); const [power, setPower] = useState("0.80");
  const [plan, setPlan] = useState<Plan | null>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    const input = { proportion_a: Number(proportionA), proportion_b: Number(proportionB), alpha: Number(alpha), target_power: Number(power) };
    if (!Number.isFinite(input.proportion_a) || !Number.isFinite(input.proportion_b) || input.proportion_a < 0 || input.proportion_a > 1 || input.proportion_b < 0 || input.proportion_b > 1 || input.proportion_a === input.proportion_b || !(input.alpha >= .001 && input.alpha <= .5) || !(input.target_power > .5 && input.target_power < .999)) { setError("서로 다른 예상 불량률과 유효한 유의수준·목표 검정력을 입력하세요."); return; }
    setLoading(true); setError("");
    try { const run = await createTwoSampleProportionPowerRun({ run_id: runId, ...input }); setPlan(run.result.diagnostics as Plan); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "표본수 계획을 실행하지 못했습니다."); }
    finally { setLoading(false); }
  }
  return <div className="page form-page"><section className="page-heading"><span className="eyebrow">POWER ANALYSIS</span><h1>두 비율 표본수 계획</h1><p>두 생산라인 또는 개선 전후의 예상 불량률 차이를 검출할 검사 수를 계획합니다.</p></section>{error && <p role="alert">{error}</p>}<form className="analysis-form" onSubmit={submit}><section className="form-panel"><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} /></label><label className="field"><span>집단 A 예상 불량률</span><input value={proportionA} onChange={(event) => setProportionA(event.target.value)} /></label><label className="field"><span>집단 B 예상 불량률</span><input value={proportionB} onChange={(event) => setProportionB(event.target.value)} /></label><label className="field"><span>유의수준 α</span><input value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label><label className="field"><span>목표 검정력</span><input value={power} onChange={(event) => setPower(event.target.value)} /></label></div></section><div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>필요 검사 수 계산</Button></div></form>{plan && <section className="metric-grid result-metrics" aria-label="두 비율 표본수 계획 결과"><article className="metric-card"><span>집단별 필요 검사 수</span><strong>{plan.sample_size_per_group}</strong><small>동일한 두 집단</small></article><article className="metric-card"><span>전체 필요 검사 수</span><strong>{plan.total_sample_size}</strong><small>탈락·결측 여유분은 별도 반영</small></article><article className="metric-card"><span>검출할 절대 차이</span><strong>{(plan.absolute_difference * 100).toFixed(2)}%p</strong><small>두 예상 불량률의 차이</small></article></section>}</div>;
}

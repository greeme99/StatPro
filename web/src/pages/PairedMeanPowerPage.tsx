import { Play } from "lucide-react";
import { useState, type FormEvent } from "react";
import { createPairedMeanPowerRun } from "../api";
import { Button } from "../components/Button";

type Plan = { required_pairs: number; paired_effect_size: number };

export function PairedMeanPowerPage() {
  const [runId, setRunId] = useState(`paired-power-${Date.now()}`);
  const [difference, setDifference] = useState("1"); const [differenceStandardDeviation, setDifferenceStandardDeviation] = useState("1");
  const [alpha, setAlpha] = useState("0.05"); const [power, setPower] = useState("0.80");
  const [plan, setPlan] = useState<Plan | null>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    const input = { difference: Number(difference), difference_standard_deviation: Number(differenceStandardDeviation), alpha: Number(alpha), target_power: Number(power) };
    if (!(input.difference > 0 && input.difference_standard_deviation > 0 && input.alpha >= .001 && input.alpha <= .5 && input.target_power > .5 && input.target_power < .999)) { setError("검출할 평균차·차이의 표준편차와 유효한 유의수준·목표 검정력을 입력하세요."); return; }
    setLoading(true); setError("");
    try { const run = await createPairedMeanPowerRun({ run_id: runId, ...input }); setPlan(run.result.diagnostics as Plan); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "표본수 계획을 실행하지 못했습니다."); }
    finally { setLoading(false); }
  }
  return <div className="page form-page"><section className="page-heading"><span className="eyebrow">POWER ANALYSIS</span><h1>대응 평균 표본수 계획</h1><p>동일 제품·설비의 개선 전후 측정 차이를 검출할 필요한 쌍 수를 계획합니다.</p></section>{error && <p role="alert">{error}</p>}<form className="analysis-form" onSubmit={submit}><section className="form-panel"><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} /></label><label className="field"><span>검출할 평균차</span><input value={difference} onChange={(event) => setDifference(event.target.value)} /></label><label className="field"><span>쌍별 차이의 표준편차</span><input value={differenceStandardDeviation} onChange={(event) => setDifferenceStandardDeviation(event.target.value)} /></label><label className="field"><span>유의수준 α</span><input value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label><label className="field"><span>목표 검정력</span><input value={power} onChange={(event) => setPower(event.target.value)} /></label></div></section><div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>필요 쌍 수 계산</Button></div></form>{plan && <section className="metric-grid result-metrics" aria-label="대응 평균 표본수 계획 결과"><article className="metric-card"><span>필요 쌍 수</span><strong>{plan.required_pairs}</strong><small>전·후 측정이 모두 가능한 대상</small></article><article className="metric-card"><span>대응 효과크기</span><strong>{plan.paired_effect_size.toFixed(3)}</strong><small>평균차 ÷ 쌍별 차이의 표준편차</small></article></section>}</div>;
}

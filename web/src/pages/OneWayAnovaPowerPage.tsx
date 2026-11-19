import { Play } from "lucide-react";
import { useState, type FormEvent } from "react";
import { createOneWayAnovaPowerRun } from "../api";
import { Button } from "../components/Button";

type Plan = { sample_size_per_group: number; total_sample_size: number; achieved_power: number; effect_size: number };

export function OneWayAnovaPowerPage() {
  const [runId, setRunId] = useState(`anova-power-${Date.now()}`);
  const [groupCount, setGroupCount] = useState("4"); const [effectSize, setEffectSize] = useState("0.25");
  const [alpha, setAlpha] = useState("0.05"); const [power, setPower] = useState("0.80");
  const [plan, setPlan] = useState<Plan | null>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    const input = { group_count: Number(groupCount), effect_size: Number(effectSize), alpha: Number(alpha), target_power: Number(power) };
    if (!(Number.isInteger(input.group_count) && input.group_count >= 3 && input.group_count <= 100 && input.effect_size > 0 && input.effect_size <= 10 && input.alpha >= .001 && input.alpha <= .5 && input.target_power > .5 && input.target_power < .999)) { setError("3~100개 집단과 유효한 Cohen의 f·유의수준·목표 검정력을 입력하세요."); return; }
    setLoading(true); setError("");
    try { const run = await createOneWayAnovaPowerRun({ run_id: runId, ...input }); setPlan(run.result.diagnostics as Plan); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "ANOVA 표본수 계획을 실행하지 못했습니다."); }
    finally { setLoading(false); }
  }
  return <div className="page form-page"><section className="page-heading"><span className="eyebrow">검정력 분석</span><h1>ANOVA 검정력·표본수 계획</h1><p>세 집단 이상 평균의 전체 차이를 검출할 균형 일원 분산분석 표본 수를 계획합니다.</p></section>{error && <p role="alert">{error}</p>}<form className="analysis-form" onSubmit={submit}><section className="form-panel"><div className="inline-fields"><label className="field"><span>분석 실행 ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} /></label><label className="field"><span>집단 수</span><input type="number" min="3" max="100" step="1" value={groupCount} onChange={(event) => setGroupCount(event.target.value)} /></label><label className="field"><span>Cohen의 f 효과크기</span><input type="number" min="0.001" max="10" step="0.001" value={effectSize} onChange={(event) => setEffectSize(event.target.value)} /><small>집단 평균의 표준편차 ÷ 공통 집단 내 표준편차</small></label><label className="field"><span>유의수준 α</span><input type="number" min="0.001" max="0.5" step="0.001" value={alpha} onChange={(event) => setAlpha(event.target.value)} /></label><label className="field"><span>목표 검정력</span><input type="number" min="0.501" max="0.998" step="0.001" value={power} onChange={(event) => setPower(event.target.value)} /></label></div></section><div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>필요 표본 수 계산</Button></div></form>{plan && <section className="metric-grid result-metrics" aria-label="ANOVA 검정력·표본수 계획 결과"><article className="metric-card"><span>집단별 필요 표본 수</span><strong>{plan.sample_size_per_group}</strong><small>모든 집단을 같은 크기로 계획</small></article><article className="metric-card"><span>전체 필요 표본 수</span><strong>{plan.total_sample_size}</strong><small>탈락·결측 여유분은 별도 반영</small></article><article className="metric-card"><span>반올림 후 검정력</span><strong>{(plan.achieved_power * 100).toFixed(1)}%</strong><small>비중심 F 분포 기준</small></article><article className="metric-card"><span>Cohen의 f</span><strong>{plan.effect_size.toFixed(3)}</strong><small>전체 평균 차이의 표준화 효과</small></article></section>}</div>;
}

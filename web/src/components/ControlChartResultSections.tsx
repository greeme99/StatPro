import { AlertTriangle, CheckCircle2, ChartNoAxesColumnIncreasing } from "lucide-react";

export type ControlLimit = {
  label: string;
  value: number | string;
};

function displayValue(value: number | string) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(4) : value;
}

export function ControlLimitBadges({ limits }: { limits: ControlLimit[] }) {
  return (
    <div className="control-limit-badges" aria-label="관리 한계">
      {limits.map((limit) => <span className={limit.label === "CL" ? "control-limit-badge is-center" : "control-limit-badge"} key={limit.label}>{limit.label} {displayValue(limit.value)}</span>)}
    </div>
  );
}

export function ControlChartStatistics({
  center,
  ucl,
  lcl,
  totalPoints,
  signalCount,
}: {
  center: number | string;
  ucl: number | string;
  lcl: number | string;
  totalPoints: number;
  signalCount: number;
}) {
  const inControlRate = totalPoints === 0 ? 0 : (totalPoints - signalCount) / totalPoints * 100;
  return (
    <section className="metric-grid result-metrics" aria-label="관리도 통계">
      <article className="metric-card"><ChartNoAxesColumnIncreasing aria-hidden="true" /><span>중심선(CL)</span><strong>{displayValue(center)}</strong><small>기준선</small></article>
      <article className="metric-card"><AlertTriangle aria-hidden="true" /><span>관리상한(UCL)</span><strong>{displayValue(ucl)}</strong><small>조사 상한</small></article>
      <article className="metric-card"><AlertTriangle aria-hidden="true" /><span>관리하한(LCL)</span><strong>{displayValue(lcl)}</strong><small>조사 하한</small></article>
      <article className="metric-card"><CheckCircle2 aria-hidden="true" /><span>관리 한계 내 점</span><strong>{inControlRate.toFixed(1)}%</strong><small>{signalCount ? `${signalCount}개 신호` : "신호 없음"}</small></article>
    </section>
  );
}

export function ControlSignalSummary({ signalCount, detail }: { signalCount: number; detail?: string }) {
  const inControl = signalCount === 0;
  return (
    <section className={inControl ? "signal-summary is-normal" : "signal-summary is-alert"} aria-label="이상 신호 분석">
      {inControl ? <CheckCircle2 aria-hidden="true" /> : <AlertTriangle aria-hidden="true" />}
      <div><h2>{inControl ? "공정이 통계적 관리 상태입니다" : "이상 신호를 검토하세요"}</h2><p>{inControl ? "관리 한계 이탈이 발견되지 않았습니다. 공정 조건과 데이터 수집 방법이 동일한지 계속 확인하세요." : detail ?? `${signalCount}개 관측값이 관리 한계 또는 선택한 보조 규칙을 벗어났습니다. 원인 조사 전 결과만으로 공정 원인을 단정하지 마세요.`}</p></div>
    </section>
  );
}

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { AttributeChartPoint } from "../analysis";

function SignalDot({
  cx,
  cy,
  payload,
}: {
  cx?: number;
  cy?: number;
  payload?: AttributeChartPoint;
}) {
  if (typeof cx !== "number" || typeof cy !== "number" || !payload) return <g />;
  return (
    <circle
      cx={cx}
      cy={cy}
      r={payload.signal ? 5 : 3}
      fill={payload.signal ? "var(--color-status-danger)" : "var(--chart-1)"}
      stroke="var(--color-bg-raised)"
      strokeWidth={payload.signal ? 2 : 0}
    />
  );
}

export function AttributeControlChart({
  points,
  chart,
}: {
  points: AttributeChartPoint[];
  chart: "p" | "np" | "c" | "u" | "p_prime" | "u_prime";
}) {
  const signalCount = points.filter((point) => point.signal).length;
  const statisticLabel = { p: "부적합률", np: "부적합품 수", c: "결점 수", u: "단위당 결점 수", p_prime: "Laney 보정 부적합률", u_prime: "Laney 보정 단위당 결점 수" }[chart];
  const summary = `${chart} 관리도, 부분군 ${points.length}개, 3시그마 한계 이탈 ${signalCount}개. 표본 크기에 따라 각 점의 관리한계가 계산됩니다.`;
  return (
    <div className="process-rail-wrap">
      <div className="process-rail" role="img" aria-label={summary}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid vertical={false} stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis dataKey="index" stroke="var(--color-border-strong)" tick={{ fill: "var(--color-text-secondary)" }} />
            <YAxis
              domain={["auto", "auto"]}
              stroke="var(--color-border-strong)"
              tick={{ fill: "var(--color-text-secondary)" }}
              tickFormatter={(value: number) => value.toFixed(chart === "np" || chart === "c" ? 1 : 3)}
              width={64}
            />
            <Tooltip
              contentStyle={{
                background: "var(--color-bg-raised)",
                border: "var(--border-width) solid var(--color-border)",
                borderRadius: "var(--radius-md)",
              }}
            />
            <Line type="linear" dataKey="ucl" name="UCL" stroke="var(--color-status-danger)" strokeDasharray="4 4" dot={false} />
            <Line type="linear" dataKey="center" name="CL" stroke="var(--color-text-secondary)" dot={false} />
            <Line type="linear" dataKey="lcl" name="LCL" stroke="var(--color-status-danger)" strokeDasharray="4 4" dot={false} />
            <Line type="linear" dataKey="statistic" name={statisticLabel} stroke="var(--chart-1)" strokeWidth={2} dot={<SignalDot />} activeDot={{ r: 5 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <caption>{chart} 관리도 차트 데이터</caption>
        <thead><tr><th scope="col">부분군</th><th scope="col">{statisticLabel}</th><th scope="col">LCL</th><th scope="col">CL</th><th scope="col">UCL</th><th scope="col">상태</th></tr></thead>
        <tbody>{points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{point.statistic}</td><td>{point.lcl}</td><td>{point.center}</td><td>{point.ucl}</td><td>{point.signal ? "3σ 한계 이탈" : "정상"}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

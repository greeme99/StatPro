import { Bar, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ParetoRow } from "../analysis";

export function ParetoChart({ rows, threshold }: { rows: ParetoRow[]; threshold: number }) {
  return <div className="pareto-chart" role="img" aria-label={`분류별 값 막대와 누적 비율 선. 우선 기준 ${threshold}%`}>
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={rows} margin={{ top: 16, right: 32, bottom: 36, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="category" angle={-20} textAnchor="end" height={64} interval={0} />
        <YAxis yAxisId="value" />
        <YAxis yAxisId="percent" orientation="right" domain={[0, 100]} unit="%" />
        <Tooltip formatter={(value, name) => [Number(value).toFixed(1), name === "value" ? "값" : "누적 비율(%)"]} />
        <ReferenceLine yAxisId="percent" y={threshold} stroke="var(--color-status-danger)" strokeDasharray="6 4" label={`${threshold}% 기준`} />
        <Bar yAxisId="value" dataKey="value" fill="var(--color-fill-brand)" name="값" />
        <Line yAxisId="percent" type="monotone" dataKey="cumulative_percentage" stroke="var(--color-status-danger)" strokeWidth={2} dot name="누적 비율" />
      </ComposedChart>
    </ResponsiveContainer>
  </div>;
}

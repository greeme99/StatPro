import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { EwmaPoint } from "../analysis";

function SignalDot({ cx, cy, payload }: { cx?: number; cy?: number; payload?: EwmaPoint }) {
  if (typeof cx !== "number" || typeof cy !== "number" || !payload) return <g />;
  return <circle cx={cx} cy={cy} r={payload.signal ? 5 : 3} fill={payload.signal ? "var(--color-status-danger)" : "var(--chart-1)"} stroke="var(--color-bg-raised)" strokeWidth={payload.signal ? 2 : 0} />;
}

export function EwmaControlChart({ points }: { points: EwmaPoint[] }) {
  const signalCount = points.filter((point) => point.signal).length;
  const summary = `EWMA 관리도, 관측값 ${points.length}개, 시작 시점 보정 관리한계 이탈 ${signalCount}개.`;
  return <div className="process-rail-wrap">
    <div className="process-rail" role="img" aria-label={summary}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid vertical={false} stroke="var(--color-border)" strokeDasharray="3 3" />
          <XAxis dataKey="index" stroke="var(--color-border-strong)" tick={{ fill: "var(--color-text-secondary)" }} />
          <YAxis domain={["auto", "auto"]} stroke="var(--color-border-strong)" tick={{ fill: "var(--color-text-secondary)" }} tickFormatter={(value: number) => value.toFixed(2)} width={64} />
          <Tooltip contentStyle={{ background: "var(--color-bg-raised)", border: "var(--border-width) solid var(--color-border)", borderRadius: "var(--radius-md)" }} />
          <Line type="linear" dataKey="ucl" name="UCL" stroke="var(--color-status-danger)" strokeDasharray="4 4" dot={false} />
          <Line type="linear" dataKey="center" name="CL" stroke="var(--color-text-secondary)" dot={false} />
          <Line type="linear" dataKey="lcl" name="LCL" stroke="var(--color-status-danger)" strokeDasharray="4 4" dot={false} />
          <Line type="linear" dataKey="ewma" name="EWMA" stroke="var(--chart-1)" strokeWidth={2} dot={<SignalDot />} activeDot={{ r: 5 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>;
}

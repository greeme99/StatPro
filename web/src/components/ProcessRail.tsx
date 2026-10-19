import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useEffect, useState } from "react";
import type { ProcessPoint } from "../analysis";

function supportsChartViewport() {
  return typeof window.matchMedia !== "function" || window.matchMedia("(min-width: 768px)").matches;
}

export function ProcessRail({
  points,
  center,
  ucl,
  lcl,
}: {
  points: ProcessPoint[];
  center: number;
  ucl: number;
  lcl: number;
}) {
  const [viewportSupported, setViewportSupported] = useState(supportsChartViewport);
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const query = window.matchMedia("(min-width: 768px)");
    const update = () => setViewportSupported(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  if (!viewportSupported) return null;
  const summary = `관측값 ${points.length}개. 중심선 ${center.toFixed(3)}, 관리상한 ${ucl.toFixed(3)}, 관리하한 ${lcl.toFixed(3)}.`;
  return (
    <div className="process-rail-wrap">
      <div className="process-rail" role="img" aria-label={summary}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 16, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid vertical={false} stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis dataKey="index" stroke="var(--color-border-strong)" tick={{ fill: "var(--color-text-secondary)" }} />
            <YAxis
              domain={[
                (dataMin: number) => Math.min(dataMin, lcl),
                (dataMax: number) => Math.max(dataMax, ucl),
              ]}
              stroke="var(--color-border-strong)"
              tick={{ fill: "var(--color-text-secondary)" }}
              tickFormatter={(value: number) => value.toFixed(2)}
              width={64}
            />
            <Tooltip contentStyle={{ background: "var(--color-bg-raised)", border: "var(--border-width) solid var(--color-border)", borderRadius: "var(--radius-md)" }} />
            <ReferenceLine y={ucl} stroke="var(--color-status-danger)" strokeDasharray="4 4" label={{ value: "UCL", position: "insideTopLeft", fill: "var(--color-status-danger)" }} />
            <ReferenceLine y={center} stroke="var(--color-text-secondary)" label={{ value: "CL", position: "insideTopLeft", fill: "var(--color-text-secondary)" }} />
            <ReferenceLine y={lcl} stroke="var(--color-status-danger)" strokeDasharray="4 4" label={{ value: "LCL", position: "insideBottomLeft", fill: "var(--color-status-danger)" }} />
            <Line type="linear" dataKey="value" stroke="var(--chart-1)" strokeWidth={2} dot={{ r: 3, fill: "var(--chart-1)" }} activeDot={{ r: 5 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <caption>관리도 차트 데이터</caption>
        <thead><tr><th scope="col">순서</th><th scope="col">관측값</th><th scope="col">상태</th></tr></thead>
        <tbody>{points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{point.value}</td><td>{point.signal ? "한계 이탈" : "정상"}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

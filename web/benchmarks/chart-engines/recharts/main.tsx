import React from "react";
import { createRoot } from "react-dom/client";
import { CartesianGrid, Line, LineChart, ReferenceLine, XAxis, YAxis } from "recharts";

const points = Array.from({ length: 1_000 }, (_, index) => ({
  index: index + 1,
  value: 10 + Math.sin(index / 21) * 0.2,
}));

createRoot(document.getElementById("root")!).render(
  <LineChart width={1200} height={600} data={points}>
    <CartesianGrid vertical={false} />
    <XAxis dataKey="index" />
    <YAxis />
    <ReferenceLine y={10.6} />
    <ReferenceLine y={10} />
    <ReferenceLine y={9.4} />
    <Line dataKey="value" dot={false} isAnimationActive={false} />
  </LineChart>,
);

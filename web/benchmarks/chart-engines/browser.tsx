import React from "react";
import { createRoot } from "react-dom/client";
import { flushSync } from "react-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts";
import { LineChart as EChartsLineChart } from "echarts/charts";
import { AriaComponent, GridComponent, MarkLineComponent } from "echarts/components";
import { init, use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";

use([EChartsLineChart, AriaComponent, GridComponent, MarkLineComponent, SVGRenderer]);

type Point = { index: number; value: number };

function points(count: number): Point[] {
  return Array.from({ length: count }, (_, index) => ({
    index: index + 1,
    value: 10 + Math.sin(index / 21) * 0.2 + Math.cos(index / 53) * 0.05,
  }));
}

function percentile(values: number[], fraction: number) {
  const ordered = [...values].sort((left, right) => left - right);
  return ordered[Math.min(ordered.length - 1, Math.floor(ordered.length * fraction))];
}

function summarize(durations: number[], svg: string) {
  return {
    median_ms: Number(percentile(durations, 0.5).toFixed(2)),
    p95_ms: Number(percentile(durations, 0.95).toFixed(2)),
    svg_characters: svg.length,
    has_svg: svg.startsWith("<svg") || svg.includes("<svg"),
  };
}

function renderRecharts(data: Point[]) {
  const container = document.createElement("div");
  document.body.append(container);
  const start = performance.now();
  const root = createRoot(container);
  flushSync(() => root.render(
    <LineChart width={1200} height={600} data={data} accessibilityLayer>
      <CartesianGrid vertical={false} />
      <XAxis dataKey="index" />
      <YAxis />
      <ReferenceLine y={10.6} />
      <ReferenceLine y={10} />
      <ReferenceLine y={9.4} />
      <Line dataKey="value" dot={false} isAnimationActive={false} />
    </LineChart>,
  ));
  const duration = performance.now() - start;
  const svg = container.querySelector("svg")?.outerHTML ?? "";
  root.unmount();
  container.remove();
  return { duration, svg };
}

function renderECharts(data: Point[]) {
  const container = document.createElement("div");
  container.style.width = "1200px";
  container.style.height = "600px";
  document.body.append(container);
  const chart = init(container, undefined, { renderer: "svg" });
  const start = performance.now();
  chart.setOption({
    animation: false,
    aria: { enabled: true, description: "관리도 벤치마크" },
    xAxis: { type: "value" },
    yAxis: { type: "value" },
    series: [{
      type: "line",
      data: data.map((point) => [point.index, point.value]),
      showSymbol: false,
      markLine: {
        silent: true,
        symbol: "none",
        data: [{ yAxis: 10.6 }, { yAxis: 10 }, { yAxis: 9.4 }],
      },
    }],
  });
  const duration = performance.now() - start;
  const svg = container.querySelector("svg")?.outerHTML ?? "";
  chart.dispose();
  container.remove();
  return { duration, svg };
}

const cases: Record<string, unknown> = {};
for (const count of [1_000, 10_000]) {
  const data = points(count);
  const iterations = count === 1_000 ? 10 : 4;
  const recharts = Array.from({ length: iterations }, () => renderRecharts(data));
  const echarts = Array.from({ length: iterations }, () => renderECharts(data));
  cases[count] = {
    recharts: summarize(recharts.map((item) => item.duration), recharts.at(-1)!.svg),
    echarts_svg: summarize(echarts.map((item) => item.duration), echarts.at(-1)!.svg),
  };
}

document.getElementById("result")!.textContent = JSON.stringify({
  schema_version: 1,
  environment: { user_agent: navigator.userAgent },
  method: {
    dimensions: "1200x600",
    series: 1,
    animation: false,
    render_mode: "browser SVG DOM creation",
    note: "Indicative same-tab benchmark; excludes interaction and peak-memory profiling.",
  },
  cases,
}, null, 2);

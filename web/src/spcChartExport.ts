import {
  toAttributeChartView,
  toCusumView,
  toEwmaView,
  toRareEventChartView,
} from "./analysis";
import type { ResultBundle } from "./types";
import { downloadArtifact } from "./xbarRExport";

type Series = { label: string; values: number[]; color: string };

export type SpcChartExportView = {
  title: string;
  points: number[];
  center: number[];
  ucl: number[];
  lcl: number[];
  signals: boolean[];
  series: Series[];
  xLabel: string;
};

const COLORS = { background: "#ffffff", border: "#d6dbe3", grid: "#d6dbe3", text: "#172033", muted: "#64748b", primary: "#1976d2", secondary: "#7c3aed", limit: "#d92d20" } as const;

function finiteRows(values: number[][]) {
  return values.length > 0 && values.every((row) => row.length > 0 && row.every(Number.isFinite));
}

export function toSpcChartExportView(result: ResultBundle): SpcChartExportView | null {
  const ewma = toEwmaView(result);
  if (ewma) return { title: "EWMA 관리도", points: ewma.points.map((point) => point.index), center: ewma.points.map((point) => point.center), ucl: ewma.points.map((point) => point.ucl), lcl: ewma.points.map((point) => point.lcl), signals: ewma.points.map((point) => point.signal), series: [{ label: "EWMA", values: ewma.points.map((point) => point.ewma), color: COLORS.primary }], xLabel: "관측 번호" };

  const cusum = toCusumView(result);
  if (cusum) return { title: "CUSUM 관리도", points: cusum.points.map((point) => point.index), center: cusum.points.map((point) => point.center), ucl: cusum.points.map((point) => point.ucl), lcl: cusum.points.map((point) => point.lcl), signals: cusum.points.map((point) => point.signal), series: [{ label: "상측 CUSUM", values: cusum.points.map((point) => point.upperCusum), color: COLORS.primary }, { label: "하측 CUSUM", values: cusum.points.map((point) => point.lowerCusum), color: COLORS.secondary }], xLabel: "관측 번호" };

  const attribute = toAttributeChartView(result);
  if (attribute) return { title: `${attribute.chart} 관리도`, points: attribute.points.map((point) => point.index), center: attribute.points.map((point) => point.center), ucl: attribute.points.map((point) => point.ucl), lcl: attribute.points.map((point) => point.lcl), signals: attribute.points.map((point) => point.signal), series: [{ label: "통계량", values: attribute.points.map((point) => point.statistic), color: COLORS.primary }], xLabel: "부분군 번호" };

  const rare = toRareEventChartView(result);
  if (rare) return { title: `${rare.chart.toUpperCase()} 관리도`, points: rare.points.map((point) => point.index), center: rare.points.map((point) => point.center), ucl: rare.points.map((point) => point.ucl), lcl: rare.points.map((point) => point.lcl), signals: rare.points.map((point) => point.signal), series: [{ label: rare.chart === "g" ? "사건 간 기회 수" : "사건 간 시간", values: rare.points.map((point) => point.interval), color: COLORS.primary }], xLabel: "사건 번호" };
  return null;
}

function escapeXml(value: unknown) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
}

function fixed(value: number) { return Number.isFinite(value) ? value.toFixed(4) : "—"; }

export function spcChartReportSvg(runId: string, view: SpcChartExportView) {
  const allValues = [...view.series.flatMap((series) => series.values), ...view.center, ...view.ucl, ...view.lcl];
  if (!finiteRows([view.points, view.center, view.ucl, view.lcl, ...view.series.map((series) => series.values)]) || allValues.length === 0) return null;
  const rawMin = Math.min(...allValues); const rawMax = Math.max(...allValues);
  const padding = Math.max((rawMax - rawMin) * 0.12, Math.abs(rawMax || 1) * 0.02, 0.05);
  const min = rawMin - padding; const max = rawMax + padding;
  const left = 104; const right = 1120; const top = 128; const bottom = 650;
  const x = (index: number) => left + (view.points.length <= 1 ? 0 : (index * (right - left)) / (view.points.length - 1));
  const y = (value: number) => bottom - ((value - min) / (max - min || 1)) * (bottom - top);
  const grid = [0, 1, 2, 3, 4].map((tick) => { const value = min + ((max - min) * tick) / 4; const lineY = y(value); return `<line x1="${left}" y1="${lineY}" x2="${right}" y2="${lineY}" class="grid"/><text x="${left - 12}" y="${lineY + 4}" text-anchor="end" class="tick">${fixed(value)}</text>`; }).join("");
  const limits = ([{ values: view.ucl, label: "UCL", className: "limit" }, { values: view.center, label: "CL", className: "center" }, { values: view.lcl, label: "LCL", className: "limit" }] as const).map(({ values, label, className }) => `<polyline points="${values.map((value, index) => `${x(index).toFixed(2)},${y(value).toFixed(2)}`).join(" ")}" class="${className}"/><text x="${right - 4}" y="${y(values.at(-1) ?? 0) - 7}" text-anchor="end" class="limit-label">${label} ${fixed(values.at(-1) ?? 0)}</text>`).join("");
  const series = view.series.map((series) => `<polyline points="${series.values.map((value, index) => `${x(index).toFixed(2)},${y(value).toFixed(2)}`).join(" ")}" fill="none" stroke="${series.color}" stroke-width="3"/>${series.values.map((value, index) => `<circle cx="${x(index)}" cy="${y(value)}" r="${view.signals[index] ? 6 : 4}" fill="${view.signals[index] ? COLORS.limit : series.color}" stroke="${COLORS.background}" stroke-width="2"><title>${escapeXml(`${series.label} ${view.points[index]}: ${fixed(value)}`)}</title></circle>`).join("")}`).join("");
  const labels = view.points.map((point, index) => `<text x="${x(index)}" y="${bottom + 26}" text-anchor="middle" class="tick">${point}</text>`).join("");
  const legend = view.series.map((series, index) => `<circle cx="${left + index * 190}" cy="82" r="5" fill="${series.color}"/><text x="${left + 12 + index * 190}" y="87" class="tick">${escapeXml(series.label)}</text>`).join("");
  return `<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" role="img" aria-labelledby="title description"><title id="title">${escapeXml(view.title)} 결과</title><desc id="description">${escapeXml(`${runId} · 관측 ${view.points.length}개 · 신호 ${view.signals.filter(Boolean).length}개`)}</desc><style>.page{fill:${COLORS.background}}.title{font:700 24px sans-serif;fill:${COLORS.text}}.meta,.tick{font:14px sans-serif;fill:${COLORS.muted}}.grid{stroke:${COLORS.grid};stroke-dasharray:3 5}.limit{fill:none;stroke:${COLORS.limit};stroke-width:2;stroke-dasharray:8 5}.center{fill:none;stroke:${COLORS.primary};stroke-width:2;stroke-dasharray:8 5}.limit-label{font:700 12px sans-serif;fill:${COLORS.limit}}</style><rect width="1200" height="760" class="page"/><text x="48" y="46" class="title">${escapeXml(view.title)} 결과</text><text x="48" y="68" class="meta">Run ID ${escapeXml(runId)} · 관측 ${view.points.length}개 · 신호 ${view.signals.filter(Boolean).length}개</text>${legend}${grid}${limits}${series}${labels}<text x="612" y="716" text-anchor="middle" class="meta">${escapeXml(view.xLabel)}</text><rect x="${left}" y="${top}" width="${right - left}" height="${bottom - top}" fill="none" stroke="${COLORS.border}"/></svg>`;
}

export function downloadSpcChartPng(runId: string, view: SpcChartExportView) {
  const svg = spcChartReportSvg(runId, view); if (!svg) return;
  const source = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml;charset=utf-8" }));
  const image = new Image();
  image.onload = () => { const canvas = document.createElement("canvas"); canvas.width = 1200; canvas.height = 760; const context = canvas.getContext("2d"); if (!context) { URL.revokeObjectURL(source); return; } context.drawImage(image, 0, 0, canvas.width, canvas.height); canvas.toBlob((blob) => { URL.revokeObjectURL(source); if (blob) downloadArtifact(`${runId}-spc-chart.png`, blob, "image/png"); }, "image/png"); };
  image.onerror = () => URL.revokeObjectURL(source); image.src = source;
}

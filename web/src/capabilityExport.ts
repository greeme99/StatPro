import { toCapabilityView } from "./analysis";
import type { ResultBundle } from "./types";
import { downloadArtifact } from "./xbarRExport";

type CapabilityMarker = { label: string; value: number; color: string };

export type CapabilityExportView = {
  title: string;
  count: number;
  location: number;
  lower: number;
  upper: number;
  intervalLabel: string;
  markers: CapabilityMarker[];
  primaryIndex: { label: string; value: number | null };
};

const COLORS = { background: "#ffffff", border: "#d6dbe3", text: "#172033", muted: "#64748b", primary: "#1976d2", band: "#dbeafe", spec: "#d92d20", target: "#7c3aed" } as const;

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function escapeXml(value: unknown) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
}

function fixed(value: number | null, digits = 4) {
  return value === null || !Number.isFinite(value) ? "—" : value.toFixed(digits);
}

export function toCapabilityExportView(result: ResultBundle): CapabilityExportView | null {
  const capability = toCapabilityView(result);
  if (!capability) return null;
  const lsl = finiteNumber(result.parameters.lsl);
  const usl = finiteNumber(result.parameters.usl);
  const target = finiteNumber(result.parameters.target);
  const lower = capability.model === "normal"
    ? capability.location - 3 * (capability.overallSigma ?? 0)
    : capability.lowerQuantile;
  const upper = capability.model === "normal"
    ? capability.location + 3 * (capability.overallSigma ?? 0)
    : capability.upperQuantile;
  if (lower === null || upper === null || !Number.isFinite(lower) || !Number.isFinite(upper) || lower >= upper) return null;
  const markers: CapabilityMarker[] = [
    ...(lsl === null ? [] : [{ label: "LSL", value: lsl, color: COLORS.spec }]),
    ...(target === null ? [] : [{ label: "목표", value: target, color: COLORS.target }]),
    ...(usl === null ? [] : [{ label: "USL", value: usl, color: COLORS.spec }]),
  ];
  const primaryIndex = capability.model === "normal"
    ? { label: "Cpk", value: capability.indices.cpk ?? null }
    : { label: "Cnpk", value: capability.indices.cnpk ?? null };
  return {
    title: capability.model === "normal" ? "정규 공정능력 분포" : "경험적 비정규 공정능력 분위수",
    count: capability.count,
    location: capability.location,
    lower,
    upper,
    intervalLabel: capability.model === "normal" ? "전체 σ 기준 ±3σ" : "경험적 0.135% ~ 99.865% 분위수",
    markers,
    primaryIndex,
  };
}

export function capabilityReportSvg(runId: string, view: CapabilityExportView) {
  const sourceValues = [view.lower, view.upper, view.location, ...view.markers.map((marker) => marker.value)];
  const rawMin = Math.min(...sourceValues); const rawMax = Math.max(...sourceValues);
  const padding = Math.max((rawMax - rawMin) * 0.1, Math.abs(rawMax || 1) * 0.02, 0.05);
  const min = rawMin - padding; const max = rawMax + padding;
  const left = 96; const right = 1110; const axisY = 424;
  const x = (value: number) => left + ((value - min) / (max - min || 1)) * (right - left);
  const ticks = [0, 1, 2, 3, 4].map((index) => {
    const value = min + ((max - min) * index) / 4;
    const position = x(value);
    return `<line x1="${position}" y1="182" x2="${position}" y2="${axisY}" class="grid"/><text x="${position}" y="${axisY + 30}" text-anchor="middle" class="tick">${fixed(value)}</text>`;
  }).join("");
  const intervalLeft = x(view.lower); const intervalRight = x(view.upper); const locationX = x(view.location);
  const markers = view.markers.map((marker, index) => {
    const position = x(marker.value); const labelY = 146 + (index % 2) * 28;
    return `<line x1="${position}" y1="${labelY + 10}" x2="${position}" y2="${axisY}" stroke="${marker.color}" stroke-width="3" stroke-dasharray="8 5"/><text x="${position}" y="${labelY}" text-anchor="middle" class="marker" fill="${marker.color}">${escapeXml(marker.label)} ${fixed(marker.value)}</text>`;
  }).join("");
  return `<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="0 0 1200 560" role="img" aria-labelledby="title description"><title id="title">${escapeXml(view.title)} 결과</title><desc id="description">${escapeXml(`${runId} · 관측 ${view.count}개 · ${view.intervalLabel} ${fixed(view.lower)}부터 ${fixed(view.upper)} · ${view.primaryIndex.label} ${fixed(view.primaryIndex.value)}`)}</desc><style>.page{fill:${COLORS.background}}.title{font:700 24px sans-serif;fill:${COLORS.text}}.meta,.tick{font:14px sans-serif;fill:${COLORS.muted}}.marker{font:700 13px sans-serif}.grid{stroke:${COLORS.border};stroke-dasharray:3 5}.axis{stroke:${COLORS.text};stroke-width:2}.band{fill:${COLORS.band};stroke:${COLORS.primary};stroke-width:2}.location{fill:${COLORS.primary}}.label{font:700 15px sans-serif;fill:${COLORS.text}}</style><rect width="1200" height="560" class="page"/><text x="48" y="48" class="title">${escapeXml(view.title)}</text><text x="48" y="72" class="meta">Run ID ${escapeXml(runId)} · 관측 ${view.count}개 · ${escapeXml(view.intervalLabel)}</text><text x="48" y="100" class="label">${escapeXml(view.primaryIndex.label)} ${fixed(view.primaryIndex.value)} · 공정 중심 ${fixed(view.location)}</text>${ticks}<line x1="${left}" y1="${axisY}" x2="${right}" y2="${axisY}" class="axis"/><rect x="${intervalLeft}" y="286" width="${Math.max(intervalRight - intervalLeft, 1)}" height="92" rx="6" class="band"/><text x="${(intervalLeft + intervalRight) / 2}" y="340" text-anchor="middle" class="label">공정 범위</text><line x1="${locationX}" y1="252" x2="${locationX}" y2="${axisY}" stroke="${COLORS.primary}" stroke-width="4"/><circle cx="${locationX}" cy="286" r="8" class="location"/><text x="${locationX}" y="240" text-anchor="middle" class="marker" fill="${COLORS.primary}">중심 ${fixed(view.location)}</text>${markers}<rect x="${left}" y="182" width="${right - left}" height="242" fill="none" stroke="${COLORS.border}"/></svg>`;
}

export function downloadCapabilityPng(runId: string, view: CapabilityExportView) {
  const source = URL.createObjectURL(new Blob([capabilityReportSvg(runId, view)], { type: "image/svg+xml;charset=utf-8" }));
  const image = new Image();
  image.onload = () => { const canvas = document.createElement("canvas"); canvas.width = 1200; canvas.height = 560; const context = canvas.getContext("2d"); if (!context) { URL.revokeObjectURL(source); return; } context.drawImage(image, 0, 0, canvas.width, canvas.height); canvas.toBlob((blob) => { URL.revokeObjectURL(source); if (blob) downloadArtifact(`${runId}-capability.png`, blob, "image/png"); }, "image/png"); };
  image.onerror = () => URL.revokeObjectURL(source); image.src = source;
}

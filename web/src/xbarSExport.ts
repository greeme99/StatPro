import type { XbarSView } from "./analysis";
import type { ResultBundle } from "./types";
import { downloadArtifact } from "./xbarRExport";

const reportColors = {
  background: "#ffffff",
  border: "#d6dbe3",
  grid: "#d6dbe3",
  text: "#172033",
  muted: "#64748b",
  series: "#1976d2",
  limit: "#d92d20",
  signal: "#d92d20",
} as const;

function escapeXml(value: unknown) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
}

function fixed(value: number) {
  return Number.isFinite(value) ? value.toFixed(4) : "—";
}

function chartPanel(title: string, points: XbarSView["xbarPoints"], limits: XbarSView["xbarLimits"], y: number) {
  const left = 96;
  const right = 1110;
  const top = y + 76;
  const bottom = y + 330;
  const values = [...points.map((point) => point.value), limits.lcl, limits.center, limits.ucl];
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const padding = Math.max((rawMax - rawMin) * 0.12, Math.abs(rawMax || 1) * 0.02, 0.05);
  const min = rawMin - padding;
  const max = rawMax + padding;
  const x = (index: number) => left + (points.length <= 1 ? 0 : (index * (right - left)) / (points.length - 1));
  const py = (value: number) => bottom - ((value - min) / (max - min)) * (bottom - top);
  const polyline = points.map((point, index) => `${x(index).toFixed(2)},${py(point.value).toFixed(2)}`).join(" ");
  const grid = [0, 1, 2, 3, 4].map((tick) => {
    const value = min + ((max - min) * tick) / 4;
    const lineY = py(value);
    return `<line x1="${left}" y1="${lineY}" x2="${right}" y2="${lineY}" class="grid"/><text x="${left - 12}" y="${lineY + 4}" text-anchor="end" class="tick">${fixed(value)}</text>`;
  }).join("");
  const limitLine = (value: number, label: string, className: string) => `<line x1="${left}" y1="${py(value)}" x2="${right}" y2="${py(value)}" class="${className}"/><text x="${right - 4}" y="${py(value) - 7}" text-anchor="end" class="limit-label">${label} ${fixed(value)}</text>`;
  const dots = points.map((point, index) => `<circle cx="${x(index)}" cy="${py(point.value)}" r="${point.signal ? 6 : 4}" class="${point.signal ? "signal-dot" : "point-dot"}"><title>부분군 ${point.index}: ${fixed(point.value)}</title></circle>`).join("");
  const labels = points.map((point, index) => `<text x="${x(index)}" y="${bottom + 24}" text-anchor="middle" class="tick">${point.index}</text>`).join("");
  return `<g aria-label="${escapeXml(title)}"><text x="48" y="${y + 35}" class="chart-title">${escapeXml(title)}</text>${grid}${limitLine(limits.ucl, "UCL", "limit")}${limitLine(limits.center, "CL", "center")}${limitLine(limits.lcl, "LCL", "limit")}<polyline points="${polyline}" class="series"/>${dots}${labels}<text x="603" y="${bottom + 52}" text-anchor="middle" class="axis-label">부분군 번호</text></g>`;
}

export function xbarSReportSvg(runId: string, view: XbarSView) {
  const signalCount = [...view.xbarPoints, ...view.sPoints].filter((point) => point.signal).length;
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900" role="img" aria-labelledby="title description">
  <title id="title">Xbar-S 관리도 결과</title><desc id="description">${escapeXml(runId)} · 부분군 ${view.xbarPoints.length}개 · 신호 ${signalCount}개</desc>
  <style>.page{fill:${reportColors.background}}.chart-title{font:700 22px sans-serif;fill:${reportColors.text}}.axis-label{font:14px sans-serif;fill:${reportColors.muted}}.tick{font:12px sans-serif;fill:${reportColors.muted}}.limit-label{font:700 12px sans-serif;fill:${reportColors.limit}}.grid{stroke:${reportColors.grid};stroke-dasharray:3 5}.series{fill:none;stroke:${reportColors.series};stroke-width:3}.point-dot{fill:${reportColors.series};stroke:${reportColors.background};stroke-width:2}.signal-dot{fill:${reportColors.signal};stroke:${reportColors.background};stroke-width:3}.limit{stroke:${reportColors.limit};stroke-width:2;stroke-dasharray:8 5}.center{stroke:${reportColors.series};stroke-width:2;stroke-dasharray:8 5}.meta{font:14px sans-serif;fill:${reportColors.muted}}</style>
  <rect width="1200" height="900" class="page"/><text x="48" y="48" class="chart-title">Xbar-S 관리도 결과</text><text x="48" y="75" class="meta">Run ID ${escapeXml(runId)} · 부분군 크기 ${view.subgroupSize} · 추정 σ ${fixed(view.estimatedSigma)} · 신호 ${signalCount}개</text>
  ${chartPanel("부분군 평균(Xbar) 관리도", view.xbarPoints, view.xbarLimits, 90)}
  ${chartPanel("부분군 표준편차(S) 관리도", view.sPoints, view.sLimits, 480)}
</svg>`;
}

export function xbarSExcelXml(runId: string, result: ResultBundle, view: XbarSView) {
  const rows = view.xbarPoints.map((point, index) => {
    const standardDeviation = view.sPoints[index];
    return `<Row><Cell><Data ss:Type="Number">${point.index}</Data></Cell><Cell><Data ss:Type="Number">${point.value}</Data></Cell><Cell><Data ss:Type="Number">${standardDeviation?.value ?? 0}</Data></Cell><Cell><Data ss:Type="String">${point.signal || standardDeviation?.signal ? "검토 필요" : "관리상태"}</Data></Cell></Row>`;
  }).join("");
  const summary = [["Run ID", runId], ["분석 유형", result.analysis_type], ["엔진 버전", result.engine_version], ["입력 SHA-256", result.input_digest], ["부분군 크기", view.subgroupSize], ["추정 σ", view.estimatedSigma]].map(([label, value]) => `<Row><Cell ss:StyleID="Header"><Data ss:Type="String">${escapeXml(label)}</Data></Cell><Cell><Data ss:Type="${typeof value === "number" ? "Number" : "String"}">${escapeXml(value)}</Data></Cell></Row>`).join("");
  return `<?xml version="1.0"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Styles><Style ss:ID="Header"><Font ss:Bold="1"/></Style></Styles><Worksheet ss:Name="요약"><Table>${summary}</Table></Worksheet><Worksheet ss:Name="부분군 결과"><Table><Row ss:StyleID="Header"><Cell><Data ss:Type="String">부분군</Data></Cell><Cell><Data ss:Type="String">평균</Data></Cell><Cell><Data ss:Type="String">표준편차</Data></Cell><Cell><Data ss:Type="String">상태</Data></Cell></Row>${rows}</Table></Worksheet></Workbook>`;
}

export function xbarSPrintHtml(runId: string, result: ResultBundle, view: XbarSView) {
  const svg = xbarSReportSvg(runId, view).replace(/^<\?xml[^>]*>\s*/, "");
  const sources = result.provenance.map((source) => `<li><a href="${escapeXml(source.url)}">${escapeXml(source.title)}</a> · ${escapeXml(source.authority)}</li>`).join("");
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>${escapeXml(runId)} Xbar-S 보고서</title><style>body{font:14px/1.6 sans-serif;color:#172033;margin:32px}h1{margin-bottom:0}.meta{color:#64748b}svg{width:100%;height:auto;border:1px solid #d6dbe3}table{border-collapse:collapse;width:100%;margin-top:24px}th,td{border:1px solid #d6dbe3;padding:8px;text-align:left}@media print{body{margin:12mm}.no-print{display:none}}</style></head><body><button class="no-print" onclick="window.print()">PDF로 저장 또는 인쇄</button><h1>Xbar-S 관리도 분석 보고서</h1><p class="meta">Run ID ${escapeXml(runId)} · 엔진 ${escapeXml(result.engine_version)} · 입력 SHA-256 ${escapeXml(result.input_digest)}</p>${svg}<h2>재현 매개변수</h2><table><tbody><tr><th>부분군 크기</th><td>${view.subgroupSize}</td><th>추정 σ</th><td>${fixed(view.estimatedSigma)}</td></tr></tbody></table><h2>근거</h2><ul>${sources || "<li>ResultBundle에 등록된 공개 근거 없음</li>"}</ul></body></html>`;
}

export function printXbarSReport(runId: string, result: ResultBundle, view: XbarSView) {
  const report = window.open("", "_blank", "popup");
  if (!report) return false;
  report.document.write(xbarSPrintHtml(runId, result, view));
  report.document.close();
  return true;
}

export function downloadXbarSPng(runId: string, view: XbarSView) {
  const svg = xbarSReportSvg(runId, view);
  const source = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml;charset=utf-8" }));
  const image = new Image();
  image.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = 1200;
    canvas.height = 900;
    const context = canvas.getContext("2d");
    if (!context) { URL.revokeObjectURL(source); return; }
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      URL.revokeObjectURL(source);
      if (blob) downloadArtifact(`${runId}-xbar-s.png`, blob, "image/png");
    }, "image/png");
  };
  image.onerror = () => URL.revokeObjectURL(source);
  image.src = source;
}

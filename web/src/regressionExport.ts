import type { ResultBundle } from "./types";
import { downloadArtifact } from "./xbarRExport";

export type RegressionExportPoint = { observation: number; fitted: number; residual: number };
export type RegressionExportView = { points: RegressionExportPoint[] };

function escapeXml(value: unknown) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
}

function fixed(value: number) {
  return Number.isFinite(value) ? value.toFixed(4) : "—";
}

/**
 * The OLS engine owns fitted_values. Export only when that fully computed table
 * is present: this prevents the UI from producing an inferred or placeholder plot.
 */
export function toRegressionExportView(result: ResultBundle): RegressionExportView | null {
  if (result.analysis_type !== "regression.linear_ols" && result.analysis_type !== "regression.polynomial_ols" && result.analysis_type !== "regression.interaction_ols") return null;
  const rows = (result.tables.fitted_values as { rows?: unknown } | undefined)?.rows;
  if (!Array.isArray(rows) || rows.length === 0) return null;
  const points = rows.map((row): RegressionExportPoint | null => {
    if (!row || typeof row !== "object") return null;
    const values = row as Record<string, unknown>;
    const observation = Number(values.observation);
    const fitted = Number(values.fitted);
    const residual = Number(values.residual);
    return [observation, fitted, residual].every(Number.isFinite) ? { observation, fitted, residual } : null;
  });
  return points.every((point): point is RegressionExportPoint => point !== null) ? { points } : null;
}

function extent(values: number[]) {
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const span = rawMax - rawMin;
  const padding = Math.max(span * 0.12, Math.abs(rawMax || rawMin || 1) * 0.02, 0.05);
  return { min: rawMin - padding, max: rawMax + padding };
}

export function regressionResidualSvg(runId: string, view: RegressionExportView) {
  const left = 112; const right = 1112; const top = 148; const bottom = 690;
  const xRange = extent(view.points.map((point) => point.fitted));
  const yRange = extent([...view.points.map((point) => point.residual), 0]);
  const x = (value: number) => left + ((value - xRange.min) / (xRange.max - xRange.min)) * (right - left);
  const y = (value: number) => bottom - ((value - yRange.min) / (yRange.max - yRange.min)) * (bottom - top);
  const xGrid = [0, 1, 2, 3, 4].map((tick) => { const value = xRange.min + ((xRange.max - xRange.min) * tick) / 4; const position = x(value); return `<line x1="${position}" y1="${top}" x2="${position}" y2="${bottom}" class="grid"/><text x="${position}" y="${bottom + 26}" text-anchor="middle" class="tick">${fixed(value)}</text>`; }).join("");
  const yGrid = [0, 1, 2, 3, 4].map((tick) => { const value = yRange.min + ((yRange.max - yRange.min) * tick) / 4; const position = y(value); return `<line x1="${left}" y1="${position}" x2="${right}" y2="${position}" class="grid"/><text x="${left - 14}" y="${position + 4}" text-anchor="end" class="tick">${fixed(value)}</text>`; }).join("");
  const dots = view.points.map((point) => `<circle cx="${x(point.fitted)}" cy="${y(point.residual)}" r="6" class="point"><title>관측 ${point.observation}: 적합값 ${fixed(point.fitted)}, 잔차 ${fixed(point.residual)}</title></circle>`).join("");
  return `<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="1200" height="820" viewBox="0 0 1200 820" role="img" aria-labelledby="title description"><title id="title">OLS 잔차 대 적합값 진단</title><desc id="description">${escapeXml(runId)} · 관측 ${view.points.length}개</desc><style>.page{fill:#ffffff}.title{font:700 26px sans-serif;fill:#172033}.meta,.tick,.axis{font:14px sans-serif;fill:#64748b}.grid{stroke:#d6dbe3;stroke-dasharray:3 5}.zero{stroke:#d92d20;stroke-width:2;stroke-dasharray:8 5}.point{fill:#1976d2;stroke:#ffffff;stroke-width:2}</style><rect width="1200" height="820" class="page"/><text x="48" y="54" class="title">OLS 잔차 대 적합값</text><text x="48" y="82" class="meta">Run ID ${escapeXml(runId)} · 관측 ${view.points.length}개 · 잔차의 무작위 분포와 분산 변화를 검토하세요.</text>${xGrid}${yGrid}<line x1="${left}" y1="${y(0)}" x2="${right}" y2="${y(0)}" class="zero"/><text x="${right - 4}" y="${y(0) - 8}" text-anchor="end" class="meta">잔차 0</text>${dots}<text x="${(left + right) / 2}" y="${bottom + 70}" text-anchor="middle" class="axis">적합값</text><text x="34" y="${(top + bottom) / 2}" text-anchor="middle" class="axis" transform="rotate(-90 34 ${(top + bottom) / 2})">잔차</text></svg>`;
}

export function downloadRegressionPng(runId: string, view: RegressionExportView) {
  const source = URL.createObjectURL(new Blob([regressionResidualSvg(runId, view)], { type: "image/svg+xml;charset=utf-8" }));
  const image = new Image();
  image.onload = () => { const canvas = document.createElement("canvas"); canvas.width = 1200; canvas.height = 820; const context = canvas.getContext("2d"); if (!context) { URL.revokeObjectURL(source); return; } context.drawImage(image, 0, 0, canvas.width, canvas.height); canvas.toBlob((blob) => { URL.revokeObjectURL(source); if (blob) downloadArtifact(`${runId}-ols-residuals.png`, blob, "image/png"); }, "image/png"); };
  image.onerror = () => URL.revokeObjectURL(source);
  image.src = source;
}

export function regressionPrintHtml(runId: string, result: ResultBundle, view: RegressionExportView) {
  const svg = regressionResidualSvg(runId, view).replace(/^<\?xml[^>]*>\s*/, "");
  const sources = result.provenance.map((source) => `<li><a href="${escapeXml(source.url)}">${escapeXml(source.title)}</a> · ${escapeXml(source.authority)}</li>`).join("");
  const collinearityRows = (result.tables.collinearity as { rows?: unknown } | undefined)?.rows;
  const fittedRows = (result.tables.fitted_values as { rows?: unknown } | undefined)?.rows;
  const collinearity = Array.isArray(collinearityRows) ? collinearityRows.filter((row): row is Record<string, unknown> => !!row && typeof row === "object") : [];
  const predictions = Array.isArray(fittedRows) ? fittedRows.filter((row): row is Record<string, unknown> => !!row && typeof row === "object" && Number.isFinite(Number(row.prediction_interval_lower)) && Number.isFinite(Number(row.prediction_interval_upper))) : [];
  const confidence = Number(result.diagnostics.prediction_interval_confidence);
  const collinearityTable = collinearity.length ? `<h2>공선성 진단</h2><table><thead><tr><th>설명변수</th><th>VIF</th><th>허용도</th></tr></thead><tbody>${collinearity.map((row) => `<tr><th>${escapeXml(row.term)}</th><td>${fixed(Number(row.vif))}</td><td>${fixed(Number(row.tolerance))}</td></tr>`).join("")}</tbody></table>` : "";
  const predictionTable = predictions.length ? `<h2>관측별 예측구간${Number.isFinite(confidence) ? ` (${(confidence * 100).toFixed(0)}%)` : ""}</h2><table><thead><tr><th>관측</th><th>적합값</th><th>하한</th><th>상한</th></tr></thead><tbody>${predictions.map((row) => `<tr><th>${escapeXml(row.observation)}</th><td>${fixed(Number(row.fitted))}</td><td>${fixed(Number(row.prediction_interval_lower))}</td><td>${fixed(Number(row.prediction_interval_upper))}</td></tr>`).join("")}</tbody></table>` : "";
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>${escapeXml(runId)} OLS 회귀 보고서</title><style>body{font:14px/1.6 sans-serif;color:#172033;margin:32px}h1{margin-bottom:0}.meta{color:#64748b}svg{width:100%;height:auto;border:1px solid #d6dbe3}table{width:100%;border-collapse:collapse;margin:16px 0}th,td{padding:6px 8px;border:1px solid #d6dbe3;text-align:left}@media print{body{margin:12mm}.no-print{display:none}}</style></head><body><button class="no-print" onclick="window.print()">PDF로 저장 또는 인쇄</button><h1>OLS 선형회귀 진단 보고서</h1><p class="meta">Run ID ${escapeXml(runId)} · 엔진 ${escapeXml(result.engine_version)} · 입력 SHA-256 ${escapeXml(result.input_digest)}</p>${svg}${collinearityTable}${predictionTable}<h2>검토 안내</h2><p>잔차가 0선을 중심으로 무작위로 분포하는지, 적합값에 따라 분산이 변하지 않는지 확인하세요. 이상 패턴이 있으면 변수 변환, 누락 요인, 비선형 항 또는 독립성 가정을 검토합니다.</p><h2>계산 근거</h2><ul>${sources || "<li>ResultBundle에 등록된 공개 근거 없음</li>"}</ul></body></html>`;
}

export function printRegressionReport(runId: string, result: ResultBundle, view: RegressionExportView) {
  const report = window.open("", "_blank", "popup");
  if (!report) return false;
  report.document.write(regressionPrintHtml(runId, result, view));
  report.document.close();
  return true;
}

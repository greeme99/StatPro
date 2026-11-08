import { Download, FileJson, FileSpreadsheet, FileText, ImageDown, ImageUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { toImrView, toXbarRView, toXbarSView } from "../analysis";
import { capabilityReportSvg, downloadCapabilityPng, toCapabilityExportView } from "../capabilityExport";
import type { ResultBundle } from "../types";
import { downloadArtifact, downloadXbarRPng, printXbarRReport, xbarRExcelXml, xbarRReportSvg } from "../xbarRExport";
import { downloadXbarSPng, printXbarSReport, xbarSExcelXml, xbarSReportSvg } from "../xbarSExport";
import { downloadImrPng, imrExcelXml, imrPrintHtml, imrReportSvg, printImrReport } from "../imrExport";
import { downloadSpcChartPng, spcChartReportSvg, toSpcChartExportView } from "../spcChartExport";
import { Button } from "./Button";

type CsvRow = [section: string, path: string, value: string];

function escapeCsvCell(value: string) {
  return `"${value.replaceAll('"', '""')}"`;
}

function flattenCsvValue(section: string, path: string, value: unknown, rows: CsvRow[]) {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    rows.push([section, path, value === null ? "" : String(value)]);
    return;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) rows.push([section, path, "[]"]);
    value.forEach((item, index) => flattenCsvValue(section, `${path}[${index}]`, item, rows));
    return;
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>).sort(([left], [right]) => left.localeCompare(right));
    if (entries.length === 0) rows.push([section, path, "{}"]);
    entries.forEach(([key, item]) => flattenCsvValue(section, path ? `${path}.${key}` : key, item, rows));
    return;
  }

  rows.push([section, path, String(value)]);
}

export function resultBundleCsv(result: ResultBundle) {
  const rows: CsvRow[] = [];
  const sections: Array<[string, unknown]> = [
    ["결과 식별", { analysis_type: result.analysis_type, engine_version: result.engine_version, input_digest: result.input_digest }],
    ["매개변수", result.parameters],
    ["진단", result.diagnostics],
    ["표", result.tables],
    ["차트", result.plots],
    ["경고", result.warnings],
    ["가정", result.assumptions],
    ["근거", result.provenance],
  ];
  sections.forEach(([section, value]) => flattenCsvValue(section, "", value, rows));
  return `\ufeff구분,경로,값\r\n${rows.map((row) => row.map(escapeCsvCell).join(",")).join("\r\n")}\r\n`;
}

function escapeXml(value: unknown) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&apos;");
}

export function resultBundleSpreadsheetXml(runId: string, result: ResultBundle) {
  const csvRows = resultBundleCsv(result).replace(/^\ufeff/, "").trim().split("\r\n").slice(1);
  const rows = csvRows.map((line) => line.match(/"((?:[^"]|"")*)","((?:[^"]|"")*)","((?:[^"]|"")*)"/)?.slice(1).map((cell) => cell.replaceAll('""', '"')) ?? []);
  const cells = [["구분", "경로", "값"], ...rows].map((row) => `<Row>${row.map((value) => `<Cell><Data ss:Type="String">${escapeXml(value)}</Data></Cell>`).join("")}</Row>`).join("");
  return `<?xml version="1.0" encoding="UTF-8"?>\n<?mso-application progid="Excel.Sheet"?>\n<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><DocumentProperties xmlns="urn:schemas-microsoft-com:office:office"><Title>${escapeXml(`${runId} 분석 결과`)}</Title><Subject>${escapeXml(result.analysis_type)}</Subject><Author>StatPro</Author></DocumentProperties><Worksheet ss:Name="결과 데이터"><Table>${cells}</Table></Worksheet></Workbook>\n`;
}

function downloadText(filename: string, text: string, type: string) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function downloadJson(filename: string, result: ResultBundle) {
  downloadText(filename, `${JSON.stringify(result, null, 2)}\n`, "application/json");
}

function escapeHtml(value: unknown) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

export function resultBundlePrintHtml(runId: string, result: ResultBundle) {
  const rows = resultBundleCsv(result).replace(/^\ufeff/, "").trim().split("\r\n").slice(1).map((line) => line.match(/"((?:[^"]|"")*)","((?:[^"]|"")*)","((?:[^"]|"")*)"/)?.slice(1).map((cell) => cell.replaceAll('""', '"')) ?? []);
  const tableRows = rows.map(([section, path, value]) => `<tr><td>${escapeHtml(section)}</td><td>${escapeHtml(path)}</td><td>${escapeHtml(value)}</td></tr>`).join("");
  const sources = result.provenance.map((source) => `<li><a href="${escapeHtml(source.url)}">${escapeHtml(source.title)}</a> · ${escapeHtml(source.authority)}</li>`).join("");
  return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>${escapeHtml(runId)} 분석 결과 보고서</title><style>body{font:14px/1.6 sans-serif;color:#172033;margin:32px}h1{margin-bottom:0}.meta{color:#64748b;word-break:break-all}table{border-collapse:collapse;width:100%;margin-top:20px;table-layout:fixed}th,td{border:1px solid #d6dbe3;padding:7px;text-align:left;vertical-align:top;word-break:break-word}th{background:#f4f7fb}@media print{body{margin:12mm}.no-print{display:none}}</style></head><body><button class="no-print" onclick="window.print()">PDF로 저장 또는 인쇄</button><h1>분석 결과 보고서</h1><p class="meta">Run ID ${escapeHtml(runId)} · 분석 유형 ${escapeHtml(result.analysis_type)} · 엔진 ${escapeHtml(result.engine_version)} · 입력 SHA-256 ${escapeHtml(result.input_digest)}</p><h2>결과 데이터</h2><table><thead><tr><th>구분</th><th>경로</th><th>값</th></tr></thead><tbody>${tableRows}</tbody></table><h2>계산 근거</h2><ul>${sources || "<li>ResultBundle에 등록된 공개 근거 없음</li>"}</ul><p class="meta">이 문서는 저장된 분석 실행을 변경하지 않는 인쇄용 투영입니다. 차트 이미지는 해당 분석에 별도 렌더러가 있을 때만 제공됩니다.</p></body></html>`;
}

function printResultBundle(runId: string, result: ResultBundle) {
  const report = window.open("", "_blank", "popup");
  if (!report) return false;
  report.document.write(resultBundlePrintHtml(runId, result)); report.document.close(); return true;
}

export function ResultExportMenu({ runId, result }: { runId: string; result: ResultBundle }) {
  const [open, setOpen] = useState(false);
  const menu = useRef<HTMLDivElement>(null);
  const xbarR = toXbarRView(result);
  const xbarS = toXbarSView(result);
  const imr = toImrView(result);
  const spcChart = toSpcChartExportView(result);
  const capability = toCapabilityExportView(result);

  useEffect(() => {
    if (!open) return;
    const onDocumentPointerDown = (event: PointerEvent) => {
      if (!menu.current?.contains(event.target as Node)) setOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onDocumentPointerDown);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("pointerdown", onDocumentPointerDown);
      document.removeEventListener("keydown", onEscape);
    };
  }, [open]);

  return (
    <div className="result-export-menu" ref={menu}>
      <Button variant="primary" icon={<Download />} aria-expanded={open} aria-haspopup="menu" onClick={() => setOpen((value) => !value)}>결과 출력</Button>
      {open && <div className="export-popover" role="menu" aria-label="결과 출력 형식">
        <button role="menuitem" onClick={() => { downloadJson(`${runId}-result.json`, result); setOpen(false); }}><FileJson aria-hidden="true" />JSON으로 저장</button>
        <button role="menuitem" title="표·차트 원본 필드를 경로와 값으로 정규화합니다. 계층 구조 전체는 JSON을 사용하세요." onClick={() => { downloadText(`${runId}-result.csv`, resultBundleCsv(result), "text/csv;charset=utf-8"); setOpen(false); }}><FileSpreadsheet aria-hidden="true" />표·차트 데이터(CSV)로 저장</button>
        {xbarR ? <>
          <button role="menuitem" onClick={() => { if (!printXbarRReport(runId, result, xbarR)) window.alert("보고서 창을 열 수 없습니다. 브라우저의 팝업 차단 설정을 확인하세요."); setOpen(false); }}><FileText aria-hidden="true" />PDF 보고서 저장·인쇄</button>
          <button role="menuitem" onClick={() => { downloadArtifact(`${runId}-xbar-r.xls`, xbarRExcelXml(runId, result, xbarR), "application/vnd.ms-excel;charset=utf-8"); setOpen(false); }}><FileSpreadsheet aria-hidden="true" />Excel로 저장</button>
          <button role="menuitem" onClick={() => { downloadXbarRPng(runId, xbarR); setOpen(false); }}><ImageDown aria-hidden="true" />차트를 PNG로 저장</button>
          <button role="menuitem" onClick={() => { downloadArtifact(`${runId}-xbar-r.svg`, xbarRReportSvg(runId, xbarR), "image/svg+xml;charset=utf-8"); setOpen(false); }}><ImageUp aria-hidden="true" />차트를 SVG로 저장</button>
        </> : xbarS ? <>
          <button role="menuitem" onClick={() => { if (!printXbarSReport(runId, result, xbarS)) window.alert("보고서 창을 열 수 없습니다. 브라우저의 팝업 차단 설정을 확인하세요."); setOpen(false); }}><FileText aria-hidden="true" />PDF 보고서 저장·인쇄</button>
          <button role="menuitem" onClick={() => { downloadArtifact(`${runId}-xbar-s.xls`, xbarSExcelXml(runId, result, xbarS), "application/vnd.ms-excel;charset=utf-8"); setOpen(false); }}><FileSpreadsheet aria-hidden="true" />Excel로 저장</button>
          <button role="menuitem" onClick={() => { downloadXbarSPng(runId, xbarS); setOpen(false); }}><ImageDown aria-hidden="true" />차트를 PNG로 저장</button>
          <button role="menuitem" onClick={() => { downloadArtifact(`${runId}-xbar-s.svg`, xbarSReportSvg(runId, xbarS), "image/svg+xml;charset=utf-8"); setOpen(false); }}><ImageUp aria-hidden="true" />차트를 SVG로 저장</button>
        </> : imr ? <>
          <button role="menuitem" onClick={() => { if (!printImrReport(runId, result, imr)) window.alert("보고서 창을 열 수 없습니다. 브라우저의 팝업 차단 설정을 확인하세요."); setOpen(false); }}><FileText aria-hidden="true" />PDF 보고서 저장·인쇄</button>
          <button role="menuitem" onClick={() => { downloadArtifact(`${runId}-imr.xls`, imrExcelXml(runId, result, imr), "application/vnd.ms-excel;charset=utf-8"); setOpen(false); }}><FileSpreadsheet aria-hidden="true" />Excel로 저장</button>
          <button role="menuitem" onClick={() => { downloadImrPng(runId, imr); setOpen(false); }}><ImageDown aria-hidden="true" />차트를 PNG로 저장</button>
          <button role="menuitem" onClick={() => { downloadArtifact(`${runId}-imr.svg`, imrReportSvg(runId, imr), "image/svg+xml;charset=utf-8"); setOpen(false); }}><ImageUp aria-hidden="true" />차트를 SVG로 저장</button>
        </> : capability ? <>
          <button role="menuitem" onClick={() => { if (!printResultBundle(runId, result)) window.alert("보고서 창을 열 수 없습니다. 브라우저의 팝업 차단 설정을 확인하세요."); setOpen(false); }}><FileText aria-hidden="true" />PDF 보고서 저장·인쇄</button>
          <button role="menuitem" title="모든 ResultBundle 필드를 단일 시트 경로·값 표로 저장합니다. 원래 계층 구조는 JSON으로 확인하세요." onClick={() => { downloadArtifact(`${runId}-result.xls`, resultBundleSpreadsheetXml(runId, result), "application/vnd.ms-excel;charset=utf-8"); setOpen(false); }}><FileSpreadsheet aria-hidden="true" />Excel 호환 표로 저장</button>
          <button role="menuitem" onClick={() => { downloadCapabilityPng(runId, capability); setOpen(false); }}><ImageDown aria-hidden="true" />차트를 PNG로 저장</button>
          <button role="menuitem" onClick={() => { downloadArtifact(`${runId}-capability.svg`, capabilityReportSvg(runId, capability), "image/svg+xml;charset=utf-8"); setOpen(false); }}><ImageUp aria-hidden="true" />차트를 SVG로 저장</button>
        </> : spcChart ? <>
          <button role="menuitem" onClick={() => { if (!printResultBundle(runId, result)) window.alert("보고서 창을 열 수 없습니다. 브라우저의 팝업 차단 설정을 확인하세요."); setOpen(false); }}><FileText aria-hidden="true" />PDF 보고서 저장·인쇄</button>
          <button role="menuitem" title="모든 ResultBundle 필드를 단일 시트 경로·값 표로 저장합니다. 원래 계층 구조는 JSON으로 확인하세요." onClick={() => { downloadArtifact(`${runId}-result.xls`, resultBundleSpreadsheetXml(runId, result), "application/vnd.ms-excel;charset=utf-8"); setOpen(false); }}><FileSpreadsheet aria-hidden="true" />Excel 호환 표로 저장</button>
          <button role="menuitem" onClick={() => { downloadSpcChartPng(runId, spcChart); setOpen(false); }}><ImageDown aria-hidden="true" />차트를 PNG로 저장</button>
          <button role="menuitem" onClick={() => { const svg = spcChartReportSvg(runId, spcChart); if (svg) downloadArtifact(`${runId}-spc-chart.svg`, svg, "image/svg+xml;charset=utf-8"); setOpen(false); }}><ImageUp aria-hidden="true" />차트를 SVG로 저장</button>
        </> : <>
          <button role="menuitem" onClick={() => { if (!printResultBundle(runId, result)) window.alert("보고서 창을 열 수 없습니다. 브라우저의 팝업 차단 설정을 확인하세요."); setOpen(false); }}><FileText aria-hidden="true" />PDF 보고서 저장·인쇄</button>
          <button role="menuitem" title="모든 ResultBundle 필드를 단일 시트 경로·값 표로 저장합니다. 원래 계층 구조는 JSON으로 확인하세요." onClick={() => { downloadArtifact(`${runId}-result.xls`, resultBundleSpreadsheetXml(runId, result), "application/vnd.ms-excel;charset=utf-8"); setOpen(false); }}><FileSpreadsheet aria-hidden="true" />Excel 호환 표로 저장</button>
          <span role="menuitem" aria-disabled="true" title="개발 예정"><ImageDown aria-hidden="true" />차트를 PNG로 저장 <small>개발 예정</small></span>
          <span role="menuitem" aria-disabled="true" title="개발 예정"><ImageUp aria-hidden="true" />차트를 SVG로 저장 <small>개발 예정</small></span>
        </>}
      </div>}
    </div>
  );
}

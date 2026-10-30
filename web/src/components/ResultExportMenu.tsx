import { Download, FileJson, FileSpreadsheet, FileText, ImageDown, ImageUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ResultBundle } from "../types";
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

export function ResultExportMenu({ runId, result }: { runId: string; result: ResultBundle }) {
  const [open, setOpen] = useState(false);
  const menu = useRef<HTMLDivElement>(null);

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
        <span role="menuitem" aria-disabled="true" title="개발 예정"><FileText aria-hidden="true" />PDF 보고서 <small>개발 예정</small></span>
        <span role="menuitem" aria-disabled="true" title="개발 예정"><FileSpreadsheet aria-hidden="true" />Excel로 저장 <small>개발 예정</small></span>
        <span role="menuitem" aria-disabled="true" title="개발 예정"><ImageDown aria-hidden="true" />차트를 PNG로 저장 <small>개발 예정</small></span>
        <span role="menuitem" aria-disabled="true" title="개발 예정"><ImageUp aria-hidden="true" />차트를 SVG로 저장 <small>개발 예정</small></span>
      </div>}
    </div>
  );
}

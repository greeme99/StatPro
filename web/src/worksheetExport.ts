import type { CellValue, WorksheetSnapshot } from "./types";
import { downloadArtifact } from "./xbarRExport";

function escapeSpreadsheetFormula(value: string) {
  return /^[=+\-@]/.test(value) ? `'${value}` : value;
}

function csvCell(value: CellValue | string) {
  const text = value === null ? "" : escapeSpreadsheetFormula(String(value));
  return `"${text.replaceAll('"', '""')}"`;
}

/** Serializes the saved current revision; it never re-parses or mutates the worksheet. */
export function worksheetCsv(worksheet: WorksheetSnapshot) {
  const header = worksheet.columns.map((column) => csvCell(column.name)).join(",");
  const rows = Array.from({ length: worksheet.row_count }, (_, rowIndex) => worksheet.columns
    .map((column) => csvCell(column.values[rowIndex]))
    .join(","));
  return `\ufeff${header}\r\n${rows.join("\r\n")}\r\n`;
}

export function downloadWorksheetCsv(worksheet: WorksheetSnapshot) {
  downloadArtifact(`${worksheet.worksheet_id}-r${worksheet.revision}.csv`, worksheetCsv(worksheet), "text/csv;charset=utf-8");
}

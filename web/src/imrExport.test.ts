import { describe, expect, it } from "vitest";
import { toImrView } from "./analysis";
import { imrExcelXml, imrPrintHtml, imrReportSvg } from "./imrExport";
import type { ResultBundle } from "./types";

const result: ResultBundle = { analysis_type: "spc.imr", engine_version: "0.6.0", input_digest: "c".repeat(64), parameters: { rules: "nelson" }, tables: { limits: { individuals: { center: 10, lcl: 9, ucl: 11 }, moving_range: { center: 0.5, lcl: 0, ucl: 1.7 } } }, plots: { individuals: { values: [9.8, 10.3, 10.1], signals: [1], rule_signals: [{ rule: "test_1", involved_indices: [0] }] }, moving_range: { values: [0.5, 0.2], signals: [] } }, diagnostics: {}, warnings: [], assumptions: [], provenance: [{ title: "NIST I-MR", url: "https://example.test/imr", authority: "NIST" }] };

describe("I-MR standard artifacts", () => {
  const view = toImrView(result)!;
  it("creates an accessible combined SVG for individuals and moving range", () => {
    const svg = imrReportSvg("run-imr", view);
    expect(svg).toContain("개별값(I) 관리도"); expect(svg).toContain("이동범위(MR) 관리도"); expect(svg).toContain("Run ID run-imr");
  });
  it("creates Excel and printable HTML with result provenance", () => {
    expect(imrExcelXml("run-imr", result, view)).toContain('Worksheet ss:Name="관측 결과"');
    const report = imrPrintHtml("run-imr", result, view);
    expect(report).toContain("PDF로 저장 또는 인쇄"); expect(report).toContain("NIST I-MR"); expect(report).toContain("입력 SHA-256");
  });
});

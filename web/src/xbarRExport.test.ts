import { describe, expect, it } from "vitest";
import { toXbarRView } from "./analysis";
import type { ResultBundle } from "./types";
import { xbarRExcelXml, xbarRPrintHtml, xbarRReportSvg } from "./xbarRExport";

const result: ResultBundle = {
  analysis_type: "spc.xbar_r",
  engine_version: "0.6.0",
  input_digest: "a".repeat(64),
  parameters: { subgroup_size: 5, a2: 0.577, d3: 0, d4: 2.114, rules: "nelson" },
  tables: { limits: { xbar: { center: 10, lcl: 9.5, ucl: 10.5 }, range: { center: 0.8, lcl: 0, ucl: 1.7 } } },
  plots: {
    xbar: { values: [9.8, 10.2, 10.6], signals: [2], rule_signals: [{ rule: "NELSON-1", involved_indices: [2] }] },
    range: { values: [0.7, 0.9, 0.8], signals: [], rule_signals: [] },
  },
  diagnostics: {},
  assumptions: ["합리적 부분군"],
  warnings: [],
  provenance: [{ title: "NIST Xbar-R", url: "https://example.test/xbar-r", authority: "NIST" }],
};

describe("Xbar-R standard artifacts", () => {
  const view = toXbarRView(result);

  it("preserves rule evidence in the view and combined SVG", () => {
    expect(view?.xbarPoints[2].rules).toEqual(["NELSON-1"]);
    const svg = xbarRReportSvg("run-xbar-r", view!);
    expect(svg).toContain("부분군 평균(Xbar) 관리도");
    expect(svg).toContain("부분군 범위(R) 관리도");
    expect(svg).toContain("NELSON-1");
    expect(svg).toContain("Run ID run-xbar-r");
  });

  it("creates an Excel workbook with summary and subgroup evidence", () => {
    const workbook = xbarRExcelXml("run-xbar-r", result, view!);
    expect(workbook).toContain('Worksheet ss:Name="요약"');
    expect(workbook).toContain('Worksheet ss:Name="부분군 결과"');
    expect(workbook).toContain("NELSON-1");
    expect(workbook).toContain(result.input_digest);
  });

  it("creates a print-ready report with reproducibility and provenance", () => {
    const report = xbarRPrintHtml("run-xbar-r", result, view!);
    expect(report).toContain("PDF로 저장 또는 인쇄");
    expect(report).toContain("입력 SHA-256");
    expect(report).toContain("NIST Xbar-R");
    expect(report).toContain("A2");
  });
});

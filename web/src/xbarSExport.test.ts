import { describe, expect, it } from "vitest";
import { toXbarSView } from "./analysis";
import type { ResultBundle } from "./types";
import { xbarSExcelXml, xbarSPrintHtml, xbarSReportSvg } from "./xbarSExport";

const result: ResultBundle = {
  analysis_type: "spc.xbar_s",
  engine_version: "0.6.0",
  input_digest: "b".repeat(64),
  parameters: { subgroup_size: 10, rules: "nelson" },
  tables: { limits: { xbar: { center: 10, lcl: 9.5, ucl: 10.5 }, standard_deviation: { center: 0.8, lcl: 0.2, ucl: 1.4 } } },
  plots: { xbar: { values: [9.8, 10.2, 10.6], signals: [2] }, standard_deviation: { values: [0.7, 0.9, 0.8], signals: [] } },
  diagnostics: { estimated_sigma: 0.75 },
  assumptions: ["합리적 부분군"],
  warnings: [],
  provenance: [{ title: "NIST Xbar-S", url: "https://example.test/xbar-s", authority: "NIST" }],
};

describe("Xbar-S standard artifacts", () => {
  const view = toXbarSView(result);

  it("creates an accessible combined SVG with both charts", () => {
    const svg = xbarSReportSvg("run-xbar-s", view!);
    expect(svg).toContain("부분군 평균(Xbar) 관리도");
    expect(svg).toContain("부분군 표준편차(S) 관리도");
    expect(svg).toContain("추정 σ 0.7500");
    expect(svg).toContain("Run ID run-xbar-s");
  });

  it("creates an Excel workbook and printable report with provenance", () => {
    expect(xbarSExcelXml("run-xbar-s", result, view!)).toContain('Worksheet ss:Name="부분군 결과"');
    const report = xbarSPrintHtml("run-xbar-s", result, view!);
    expect(report).toContain("PDF로 저장 또는 인쇄");
    expect(report).toContain("NIST Xbar-S");
    expect(report).toContain("입력 SHA-256");
  });
});

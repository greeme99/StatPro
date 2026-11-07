import { describe, expect, it } from "vitest";
import { resultBundleCsv, resultBundlePrintHtml } from "./ResultExportMenu";

describe("resultBundleCsv", () => {
  it("serializes result tables and chart source data in deterministic path-value rows", () => {
    const csv = resultBundleCsv({
      analysis_type: "spc.xbar_r",
      engine_version: "0.6.0",
      input_digest: "digest-1",
      parameters: { subgroup_size: 5 },
      diagnostics: { in_control: true },
      tables: { points: [{ subgroup: 1, mean: 10.1 }] },
      plots: { xbar: { series: [10.1, 10.2] } },
      assumptions: ["동일 부분군 크기"],
      warnings: [],
      provenance: [{ title: "NIST", url: "https://example.test/nist", authority: "NIST" }],
    });

    expect(csv).toContain("\ufeff구분,경로,값\r\n");
    expect(csv).toContain('"표","points[0].mean","10.1"');
    expect(csv).toContain('"차트","xbar.series[1]","10.2"');
    expect(csv).toContain('"근거","[0].authority","NIST"');
    expect(csv.indexOf('"결과 식별","analysis_type"')).toBeLessThan(csv.indexOf('"매개변수","subgroup_size"'));
  });

  it("projects every stored result into a printable report with identity and provenance", () => {
    const result = {
      analysis_type: "msa.gage_rr_nested",
      engine_version: "0.6.0",
      input_digest: "digest-2",
      parameters: { design: "nested" },
      diagnostics: { balanced: true },
      tables: { variance_components: { repeatability: 2 } },
      plots: {},
      warnings: ["설명적 결과입니다."],
      assumptions: ["균형 중첩 설계"],
      provenance: [{ title: "Minitab nested Gage R&R", url: "https://example.test/nested", authority: "Minitab" }],
    };

    const report = resultBundlePrintHtml("nested-001", result);
    expect(report).toContain("Run ID nested-001");
    expect(report).toContain("입력 SHA-256 digest-2");
    expect(report).toContain("variance_components.repeatability");
    expect(report).toContain("Minitab nested Gage R&amp;R");
    expect(report).toContain("PDF로 저장 또는 인쇄");
  });
});

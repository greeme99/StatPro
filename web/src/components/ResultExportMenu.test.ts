import { describe, expect, it } from "vitest";
import { resultBundleCsv } from "./ResultExportMenu";

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
});

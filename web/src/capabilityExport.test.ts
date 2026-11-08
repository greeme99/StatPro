import { describe, expect, it } from "vitest";
import { capabilityReportSvg, toCapabilityExportView } from "./capabilityExport";
import type { ResultBundle } from "./types";

const normalResult: ResultBundle = {
  analysis_type: "capability.normal_individuals", engine_version: "0.6.0", input_digest: "c".repeat(64),
  parameters: { lsl: 95, usl: 105, target: 100 }, diagnostics: {},
  tables: { summary: { count: 5, mean: 100, within_sigma: 1.1, overall_sigma: 1.6 }, indices: { cp: 1.2, cpk: 1.1 }, nonconformance: { observed_total_ppm: 0 } },
  plots: { distribution: { values: [98, 99, 100, 101, 102] } }, assumptions: [], warnings: [], provenance: [],
};

describe("capability standard artifacts", () => {
  it("projects stored capability parameters as an accessible specification-and-process SVG", () => {
    const view = toCapabilityExportView(normalResult);
    expect(view?.primaryIndex).toEqual({ label: "Cpk", value: 1.1 });
    const svg = capabilityReportSvg("capability-001", view!);
    expect(svg).toContain("정규 공정능력 분포 결과");
    expect(svg).toContain("Run ID capability-001");
    expect(svg).toContain("LSL 95.0000");
    expect(svg).toContain("USL 105.0000");
  });

  it("uses empirical tail quantiles without claiming a named distribution", () => {
    const result: ResultBundle = { ...normalResult, analysis_type: "capability.nonnormal_empirical", tables: { summary: { count: 8, median: 4, lower_quantile: 1, upper_quantile: 10, equivalent_sigma: 1.5 }, indices: { cnpk: 0.9 }, nonconformance: { observed_total_ppm: 0 } } };
    const view = toCapabilityExportView(result);
    expect(view?.intervalLabel).toContain("경험적");
    expect(capabilityReportSvg("capability-nonnormal", view!)).toContain("Cnpk 0.9000");
  });
});

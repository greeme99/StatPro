import { describe, expect, it } from "vitest";
import type { WorksheetSnapshot } from "./types";
import { worksheetCsv } from "./worksheetExport";

const worksheet: WorksheetSnapshot = {
  worksheet_id: "ws_example",
  name: "Measurements",
  base_dataset_digest: "a".repeat(64),
  digest: "b".repeat(64),
  revision: 2,
  parent_digest: "c".repeat(64),
  row_count: 2,
  columns: [
    { name: "reading", data_type: "numeric", nullable: true, missing_count: 1, values: [10.5, null] },
    { name: "note", data_type: "text", nullable: false, missing_count: 0, values: ["ok, checked", "=SUM(A1:A2)"] },
  ],
  transformations: [{ operation: "filter_rows" }],
};

describe("worksheetCsv", () => {
  it("preserves the current revision values as UTF-8 BOM CSV and neutralizes formula text", () => {
    const csv = worksheetCsv(worksheet);
    expect(csv).toBe("\ufeff\"reading\",\"note\"\r\n\"10.5\",\"ok, checked\"\r\n\"\",\"'=SUM(A1:A2)\"\r\n");
  });
});

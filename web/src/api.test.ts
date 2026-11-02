import { afterEach, describe, expect, it, vi } from "vitest";
import { createImrRun } from "./api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("analysis API response boundary", () => {
  it("explains an empty successful I-MR response instead of leaking a JSON parser error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 201 }));

    await expect(createImrRun({ run_id: "imr-empty-response", values: [10, 10.2], rules: "basic" }))
      .rejects.toThrow("분석 실행 결과가 비어 있습니다. 로컬 분석 서버 로그를 확인하세요.");
  });
});

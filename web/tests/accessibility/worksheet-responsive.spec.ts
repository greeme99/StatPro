import { expect, test } from "@playwright/test";

const worksheet = {
  worksheet_id: "responsive-audit",
  name: "SMT 순간정지 측정",
  base_dataset_digest: "d".repeat(64),
  digest: "e".repeat(64),
  revision: 3,
  parent_digest: "c".repeat(64),
  row_count: 3,
  columns: [
    { name: "설비", data_type: "text", nullable: false, missing_count: 0, values: ["M01", "M02", "M03"] },
    { name: "순간정지_초", data_type: "numeric", nullable: true, missing_count: 1, values: [4.2, null, 12.4] },
    { name: "상태", data_type: "text", nullable: false, missing_count: 0, values: ["복구", "점검", "조치 필요"] },
  ],
  transformations: [],
};

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem("statpro-demo-authenticated", "true");
    localStorage.setItem("statpro-theme", "light");
  });
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const body = pathname === "/api/health"
      ? { ok: true, engine_version: "responsive-test", local_only: true }
      : pathname === "/api/v1/worksheets/responsive-audit"
        ? { worksheet_id: worksheet.worksheet_id, storage_version: 3, etag: "f".repeat(64), worksheet, dataset: null }
        : { items: [], next_cursor: null };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
});

test("1024px 작업표에서 도구를 2열로 유지하고 열 선택을 키보드로 수행한다", async ({ page }) => {
  await page.setViewportSize({ width: 1024, height: 900 });
  await page.goto("/data/responsive-audit");
  const table = page.getByRole("table", { name: "SMT 순간정지 측정 데이터, 3행 3열" });
  await expect(table).toBeVisible();
  await expect(page.locator(".worksheet-tools-grid")).toHaveCSS("grid-template-columns", /.+\s.+/);

  const column = page.getByRole("button", { name: /순간정지_초/ });
  await column.focus();
  await page.keyboard.press("Enter");
  await expect(column).toHaveAttribute("aria-pressed", "true");
});

test("768px 작업표에서 도구를 한 열로 전환한다", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 900 });
  await page.goto("/data/responsive-audit");
  await expect(page.getByRole("table", { name: "SMT 순간정지 측정 데이터, 3행 3열" })).toBeVisible();
  const columns = await page.locator(".worksheet-tools-grid").evaluate((element) => getComputedStyle(element).gridTemplateColumns.trim().split(/\s+/).length);
  expect(columns).toBe(1);
});

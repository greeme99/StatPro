import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const pages = [
  ["홈", "/home"],
  ["작업표 및 데이터", "/data"],
  ["분석 선택", "/analyses"],
  ["결과 및 보고서", "/catalog/reports"],
] as const;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem("statpro-demo-authenticated", "true");
    localStorage.setItem("statpro-theme", "light");
    localStorage.setItem("statpro-sidebar-collapsed", "false");
  });
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const body = pathname === "/api/health"
      ? { ok: true, engine_version: "wcag-test", local_only: true }
      : pathname === "/api/v1/worksheets"
        ? { items: [], next_cursor: null }
        : { items: [], next_cursor: null };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
});

for (const [name, path] of pages) {
  test(`${name}에 serious/critical WCAG 2.1 AA 위반이 없다`, async ({ page }, testInfo) => {
    await page.goto(path);
    await expect(page.locator("#main-content h1").first()).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    const blockingViolations = results.violations.filter(({ impact }) => impact === "serious" || impact === "critical");

    await testInfo.attach("axe-results", {
      body: JSON.stringify(results, null, 2),
      contentType: "application/json",
    });
    expect(blockingViolations, JSON.stringify(blockingViolations, null, 2)).toEqual([]);
  });
}

import { expect, test } from "@playwright/test";

const pages = [
  ["home", "/home"],
  ["data", "/data"],
  ["analyses", "/analyses"],
  ["reports", "/catalog/reports"],
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
      ? { ok: true, engine_version: "visual-test", local_only: true }
      : { items: [], next_cursor: null };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
});

for (const [name, path] of pages) {
  test(`${name} 핵심 레이아웃 시각 회귀`, async ({ page }) => {
    await page.goto(path);
    const main = page.locator("#main-content");
    await expect(main.locator("h1").first()).toBeVisible();
    await expect(main).toHaveScreenshot(`${name}-main.png`, { animations: "disabled", caret: "hide" });
  });
}

import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "@playwright/test";

const phase = process.argv[2];
if (phase !== "before" && phase !== "after") throw new Error("사용법: npm run capture:ux -- before|after");

const targets = [
  ["home", "/home"],
  ["data", "/data"],
  ["analyses", "/analyses"],
  ["reports", "/catalog/reports"],
];
const outputDirectory = resolve("..", "docs", "ux-audit", "2026-11-22", "round-3", "captures");
await mkdir(outputDirectory, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const summary = [];
for (const [name, path] of targets) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: "ko-KR", colorScheme: "light", reducedMotion: "reduce" });
  await context.addInitScript(() => {
    sessionStorage.setItem("statpro-demo-authenticated", "true");
    localStorage.setItem("statpro-theme", "light");
    localStorage.setItem("statpro-sidebar-collapsed", "false");
  });
  const page = await context.newPage();
  const pageErrors = [];
  const consoleErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  await page.route("**/api/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const body = pathname === "/api/health"
      ? { ok: true, engine_version: "ux-audit", local_only: true }
      : { items: [], next_cursor: null };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
  await page.goto(`http://127.0.0.1:5173${path}`);
  await page.locator("#main-content h1").first().waitFor();
  await page.screenshot({ path: resolve(outputDirectory, `${phase}-${name}.png`), fullPage: true });
  await writeFile(resolve(outputDirectory, `${phase}-${name}-accessibility.txt`), `${await page.locator("body").ariaSnapshot()}\n`, "utf8");
  summary.push({ name, path, finalUrl: page.url(), pageErrors, consoleErrors });
  await context.close();
}
await browser.close();
await writeFile(resolve(outputDirectory, `${phase}-summary.json`), `${JSON.stringify(summary, null, 2)}\n`, "utf8");

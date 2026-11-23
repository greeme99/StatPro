import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "@playwright/test";

const phase = process.argv[2];
if (phase !== "before" && phase !== "after") throw new Error("사용법: npm run capture:ux -- before|after");

const round = process.argv[3] ?? "4";
if (!/^\d+$/.test(round)) throw new Error("개선 차수는 숫자로 입력하세요.");

const worksheet = {
  worksheet_id: "ux-audit",
  name: "SMT 순간정지 측정",
  base_dataset_digest: "d".repeat(64),
  digest: "e".repeat(64),
  revision: 3,
  parent_digest: "c".repeat(64),
  row_count: 6,
  columns: [
    { name: "설비", data_type: "text", nullable: false, missing_count: 0, values: ["M01", "M01", "M02", "M02", "M03", "M03"] },
    { name: "순간정지_초", data_type: "numeric", nullable: true, missing_count: 1, values: [4.2, 7.1, 3.8, null, 12.4, 5.6] },
    { name: "발생시각", data_type: "datetime", nullable: false, missing_count: 0, values: ["2026-11-21T08:10:00", "2026-11-21T09:25:00", "2026-11-21T10:40:00", "2026-11-21T11:55:00", "2026-11-21T13:10:00", "2026-11-21T14:25:00"] },
    { name: "상태", data_type: "text", nullable: false, missing_count: 0, values: ["복구", "점검", "복구", "점검", "조치 필요", "복구"] },
  ],
  transformations: [],
};

const targets = [
  ["home", "/home"],
  ["data", "/data"],
  ["worksheet", "/data/ux-audit"],
  ["analyses", "/analyses"],
  ["reports", "/catalog/reports"],
];
const outputDirectory = resolve("..", "docs", "ux-audit", "2026-11-22", `round-${round}`, "captures");
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
      : pathname === "/api/v1/worksheets/ux-audit"
        ? { worksheet_id: worksheet.worksheet_id, storage_version: 3, etag: "f".repeat(64), worksheet, dataset: null }
        : pathname === "/api/v1/worksheets"
          ? { items: [{ worksheet_id: worksheet.worksheet_id, storage_version: 3, etag: "f".repeat(64), worksheet, dataset: null }], next_cursor: null }
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

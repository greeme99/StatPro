import { build } from "vite";
import { gzipSync } from "node:zlib";
import { mkdtemp, readFile, readdir, rm, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
const here = new URL(".", import.meta.url).pathname.replace(/^\/(.:)/, "$1");

async function bundle(engine, tempRoot) {
  const output = join(tempRoot, engine);
  await build({
    configFile: false,
    root: resolve(here, engine),
    logLevel: "silent",
    build: { outDir: output, emptyOutDir: true, minify: true },
  });
  const assets = join(output, "assets");
  const files = await readdir(assets);
  let raw = 0;
  let gzip = 0;
  for (const file of files.filter((name) => name.endsWith(".js"))) {
    const path = join(assets, file);
    raw += (await stat(path)).size;
    gzip += gzipSync(await readFile(path)).byteLength;
  }
  return { javascript_bytes: raw, javascript_gzip_bytes: gzip };
}

const tempRoot = await mkdtemp(join(tmpdir(), "statpro-chart-benchmark-"));
try {
  const result = {
    schema_version: 1,
    environment: { node: process.version, platform: process.platform, arch: process.arch },
    method: { note: "Bundle-only measurement. Use browser.html for render timing." },
    isolated_bundle: {
      recharts: await bundle("recharts", tempRoot),
      echarts_svg: await bundle("echarts", tempRoot),
    },
  };
  const serialized = `${JSON.stringify(result, null, 2)}\n`;
  const outputIndex = process.argv.indexOf("--output");
  if (outputIndex >= 0) await writeFile(process.argv[outputIndex + 1], serialized, "utf8");
  process.stdout.write(serialized);
} finally {
  await rm(tempRoot, { recursive: true, force: true });
}

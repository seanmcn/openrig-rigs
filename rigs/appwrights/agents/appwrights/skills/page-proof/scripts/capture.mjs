#!/usr/bin/env node
// Captures a local page at a laptop and a phone width, reports the viewport each one actually got and any
// horizontal overflow, and keeps the screenshots and the report as proof. SKILL.md beside this folder says how a
// seat uses it. Exit 0: captured, nothing overflows. 1: captured, a width overflows. 2: couldn't capture.

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { createServer } from "node:net";
import { homedir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { parseArgs } from "node:util";

const PLAYWRIGHT = process.env.PAGE_PROOF_PLAYWRIGHT_VERSION || "1.65.0";
const PHONE_BELOW = 768;
const HEIGHT = { laptop: 900, phone: 844 };
const OFFENDERS = 10;
const SERVER_TIMEOUT_MS = 60_000;
const STOP_GRACE_MS = 5_000;

class CantCapture extends Error {}

const USAGE = `usage: capture.mjs <url> [--name <state>] [--widths 1440,390] [--out <slice>/proof]
                   [--start "<command>"] [--port <n>] [--wait <selector|ms>]
       capture.mjs --probe
In --start's command and in <url>, {port} is replaced by the port (--port, or a free one with --start).`;

async function main() {
  const { values, positionals } = parseArgs({
    allowPositionals: true,
    options: {
      name: { type: "string", default: "page" },
      widths: { type: "string", default: "1440,390" },
      out: { type: "string" },
      start: { type: "string" },
      port: { type: "string" },
      wait: { type: "string" },
      probe: { type: "boolean", default: false },
      help: { type: "boolean", default: false },
    },
  });
  if (values.help) return console.log(USAGE), 0;
  if (values.probe) return probe();

  // Everything a seat can get wrong in the command is checked before anything is installed or started.
  if (positionals.length !== 1) throw new CantCapture(USAGE);
  const widths = values.widths.split(",").map((w) => Number(w.trim()));
  if (widths.some((w) => !Number.isInteger(w) || w <= 0)) {
    throw new CantCapture("--widths takes whole pixel widths, such as 1440,390");
  }
  if (values.port !== undefined && !/^\d+$/.test(values.port)) throw new CantCapture("--port takes a port number");
  if (!values.start && values.port === undefined && positionals[0].includes("{port}")) {
    throw new CantCapture("the URL has {port} in it: give --port, or --start to run the app on a free one");
  }
  const out = resolve(values.out ?? ".");
  if (basename(out) !== "proof") {
    console.error(`page-proof: writing to ${out}, not a slice's proof/ folder, so rig proof add --media can't ` +
      "attach these files: pass --out <slice>/proof (SKILL.md says where that is)");
  }

  const { chromium, version } = await loadPlaywright();
  const port = values.port ?? (values.start ? String(await freePort()) : undefined);
  const url = positionals[0].replaceAll("{port}", port);
  const server = values.start ? startServer(values.start.replaceAll("{port}", port), port) : null;
  let browser = null;
  try {
    if (server) await server.ready(url);
    browser = await launch(chromium, version);
    mkdirSync(out, { recursive: true });
    const report = { url, captured_at: new Date().toISOString(), playwright: version, widths: [] };
    for (const width of widths) {
      report.widths.push(await captureAt(browser, url, width, values, out));
    }
    writeFileSync(join(out, `${values.name}.json`), JSON.stringify(report, null, 2) + "\n");
    for (const entry of report.widths) console.log(summary(entry));
    console.log(`--media "${report.widths.map((e) => e.screenshot).join(",")}"`);
    return report.widths.some((e) => e.overflow.overflows) ? 1 : 0;
  } finally {
    if (browser) await browser.close();
    if (server) await server.stop();
  }
}

async function probe() {
  const { chromium, version } = await loadPlaywright();
  const browser = await launch(chromium, version);
  console.log(`page-proof can capture: Playwright ${version}, ${browser.version()}`);
  await browser.close();
  return 0;
}

// The repository's own Playwright when it has one, so its browser and its tests agree; otherwise a pinned
// playwright-core, installed once into the person's cache. The install lands in a folder of its own and is renamed
// into place whole, so a seat never loads a copy another seat is still installing.
async function loadPlaywright() {
  const here = createRequire(join(process.cwd(), "package.json"));
  for (const name of ["playwright", "playwright-core"]) {
    try {
      return { chromium: here(name).chromium, version: here(`${name}/package.json`).version };
    } catch {}
  }
  const cache = join(process.env.XDG_CACHE_HOME || join(homedir(), ".cache"), "page-proof", `playwright-core-${PLAYWRIGHT}`);
  if (!existsSync(cache)) {
    mkdirSync(dirname(cache), { recursive: true });
    const staging = mkdtempSync(`${cache}.installing-`);
    console.error(`page-proof: installing playwright-core@${PLAYWRIGHT} into ${cache} (once)`);
    const npm = spawnSync("npm", ["install", "--prefix", staging, "--no-save", "--no-audit", "--no-fund",
      `playwright-core@${PLAYWRIGHT}`], { stdio: ["ignore", "inherit", "inherit"] });
    if (npm.status !== 0) {
      rmSync(staging, { recursive: true, force: true });
      throw new CantCapture(`couldn't install playwright-core@${PLAYWRIGHT} with npm`);
    }
    try {
      renameSync(staging, cache);
    } catch {
      rmSync(staging, { recursive: true, force: true }); // another seat finished first; use its copy
    }
  }
  return { chromium: createRequire(join(cache, "package.json"))("playwright-core").chromium, version: PLAYWRIGHT };
}

async function launch(chromium, version) {
  try {
    return await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined });
  } catch (error) {
    const missing = /Executable doesn't exist|executable.*not found/i.test(error.message);
    throw new CantCapture(missing
      ? `no Chromium for Playwright ${version}: run \`npx playwright@${version} install chromium\`, or set CHROME_PATH`
      : `Chromium wouldn't start: ${error.message.split("\n")[0]}`);
  }
}

async function captureAt(browser, url, width, values, out) {
  const phone = width < PHONE_BELOW;
  const context = await browser.newContext({
    viewport: { width, height: phone ? HEIGHT.phone : HEIGHT.laptop },
    deviceScaleFactor: phone ? 2 : 1,
    isMobile: phone,
    hasTouch: phone,
  });
  const page = await context.newPage();
  const errors = [];
  page.on("console", (message) => message.type() === "error" && errors.push(message.text()));
  page.on("pageerror", (error) => errors.push(String(error.message || error)));
  try {
    const response = await page.goto(url, { waitUntil: "load" }).catch((error) => {
      throw new CantCapture(`couldn't load ${url}: ${error.message.split("\n")[0]}`);
    });
    if (response && !response.ok()) throw new CantCapture(`${url} answered ${response.status()}`);
    if (values.wait) {
      if (/^\d+$/.test(values.wait)) await page.waitForTimeout(Number(values.wait));
      else await page.waitForSelector(values.wait).catch(() => {
        throw new CantCapture(`${values.wait} never appeared on ${url} at ${width} px`);
      });
    }
    const measured = await page.evaluate(measure, OFFENDERS);
    const screenshot = `${values.name}-${width}.png`;
    await page.screenshot({ path: join(out, screenshot), fullPage: true });
    return { width, screenshot, ...measured, console_errors: errors };
  } finally {
    await context.close();
  }
}

// Runs in the page. An offender sticks out past the right edge of the page's visible width, and its parent
// doesn't, so the list names where the overflow starts rather than everything inside it.
function measure(limit) {
  const root = document.documentElement;
  const edge = root.clientWidth;
  const sticksOut = (el) => {
    const box = el.getBoundingClientRect();
    return box.width > 0 && box.height > 0 && box.right > edge + 0.5;
  };
  const describe = (el) => el.tagName.toLowerCase() + (el.id ? `#${el.id}` : "") +
    [...el.classList].slice(0, 2).map((c) => `.${c}`).join("");
  const offenders = [];
  for (const el of document.body ? document.body.querySelectorAll("*") : []) {
    if (offenders.length >= limit) break;
    if (sticksOut(el) && !(el.parentElement && el.parentElement !== document.body && sticksOut(el.parentElement))) {
      offenders.push({ element: describe(el), right: Math.round(el.getBoundingClientRect().right) });
    }
  }
  return {
    viewport: { width: window.innerWidth, height: window.innerHeight, device_pixel_ratio: window.devicePixelRatio },
    overflow: {
      overflows: root.scrollWidth > edge,
      scroll_width: root.scrollWidth,
      client_width: edge,
      by: Math.max(0, root.scrollWidth - edge),
      offenders,
    },
  };
}

function summary(entry) {
  const { width, height, device_pixel_ratio: dpr } = entry.viewport;
  const fit = entry.overflow.overflows
    ? `overflows by ${entry.overflow.by} px: ${entry.overflow.offenders.map((o) => o.element).join(", ") || "(no single element)"}`
    : "fits";
  const actual = width === entry.width ? "" : ` (asked for ${entry.width})`;
  const errors = entry.console_errors.length ? `, ${entry.console_errors.length} console error(s)` : "";
  return `${entry.width} px: viewport ${width}x${height} @${dpr}x${actual}, ${fit}${errors} -> ${entry.screenshot}`;
}

function freePort() {
  return new Promise((done, failed) => {
    const probe = createServer().listen(0, "127.0.0.1", () => {
      const { port } = probe.address();
      probe.close(() => done(port));
    });
    probe.on("error", failed);
  });
}

// Starts the server's command in a process group of its own and stops that whole group, whether or not the shell
// that began it is still there, so a server the command forked or left in the background stops too. It signals only
// that group, never a process found by name.
function startServer(command, port) {
  const child = spawn(command, { shell: true, detached: true, stdio: ["ignore", "inherit", "inherit"],
    env: { ...process.env, PORT: port, HOST: "127.0.0.1" } });
  const group = -child.pid;
  const signal = (name) => { try { process.kill(group, name); } catch {} };
  const running = () => { try { process.kill(group, 0); return true; } catch { return false; } };
  const stopNow = () => signal("SIGKILL");
  process.on("exit", stopNow);
  for (const name of ["SIGINT", "SIGTERM", "SIGHUP"]) {
    process.once(name, () => { signal("SIGTERM"); process.exit(2); });
  }
  return {
    async ready(url) {
      const deadline = Date.now() + SERVER_TIMEOUT_MS;
      while (Date.now() < deadline) {
        if (!running()) throw new CantCapture(`the server command ended before ${url} answered`);
        try {
          await fetch(url, { signal: AbortSignal.timeout(5_000) });
          return;
        } catch {}
        await new Promise((r) => setTimeout(r, 250));
      }
      throw new CantCapture(`${url} didn't answer within ${SERVER_TIMEOUT_MS / 1000} s of starting the server`);
    },
    async stop() {
      signal("SIGTERM");
      const deadline = Date.now() + STOP_GRACE_MS;
      while (running() && Date.now() < deadline) await new Promise((r) => setTimeout(r, 100));
      if (running()) signal("SIGKILL");
      process.off("exit", stopNow);
    },
  };
}

main().then((code) => process.exit(code), (error) => {
  console.error(`page-proof: ${error instanceof CantCapture ? error.message : error.stack || error}`);
  process.exit(2);
});

/**
 * generate-screenshots.js
 *
 * Uses Playwright to render preview-template.html with each of the 12 design
 * styles across 4 page types, producing 48 PNG screenshots in output/.
 *
 * Usage:
 *   node generate-screenshots.js
 *
 * Prerequisites:
 *   - Node.js 18+
 *   - Playwright installed with Chromium browser
 */

import { chromium } from "playwright";
import { createServer } from "http";
import { readFile } from "fs/promises";
import { existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { STYLES } from "./styles-data.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PAGES = ["landing", "dashboard", "settings", "feed"];
const VIEWPORT = { width: 1280, height: 800 };
const OUTPUT_DIR = join(__dirname, "output");

/**
 * Starts a minimal HTTP server that serves preview-template.html for any
 * request path. This avoids file:// protocol limitations with some Playwright
 * features (e.g. font loading from Google Fonts).
 *
 * Returns { server, port } so the caller can close it when done.
 */
async function startFileServer() {
  const htmlPath = join(__dirname, "preview-template.html");
  const htmlContent = await readFile(htmlPath, "utf-8");

  return new Promise((resolve, reject) => {
    const server = createServer((_req, res) => {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(htmlContent);
    });

    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      resolve({ server, port });
    });

    server.on("error", reject);
  });
}

/**
 * Injects CSS custom properties onto :root for the given style, then handles
 * style-specific quirks (glassmorphism gradient, etc.).
 */
async function applyStyle(page, styleId, styleVars) {
  await page.evaluate(
    ({ vars, id }) => {
      const root = document.documentElement;

      // Apply all CSS custom properties
      for (const [prop, value] of Object.entries(vars)) {
        root.style.setProperty(prop, value);
      }

      // Glassmorphism: set the body background to the gradient
      if (id === "glassmorphism" && vars["--canvas-gradient"]) {
        document.body.style.background = vars["--canvas-gradient"];
      } else {
        // For non-glassmorphism styles, ensure the canvas color is applied
        document.body.style.background = vars["--surface-canvas"];
      }
    },
    { vars: styleVars, id: styleId }
  );
}

/**
 * Main entry point. Launches Chromium, iterates over styles and pages,
 * captures screenshots, and writes them to output/.
 */
async function main() {
  // Ensure output directory exists
  if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const { server, port } = await startFileServer();
  const baseUrl = `http://127.0.0.1:${port}`;

  console.log(`File server started on port ${port}`);
  console.log(`Output directory: ${OUTPUT_DIR}`);
  console.log(
    `Generating ${Object.keys(STYLES).length} styles x ${PAGES.length} pages = ${Object.keys(STYLES).length * PAGES.length} screenshots\n`
  );

  const browser = await chromium.launch({
    headless: true,
    chromiumSandbox: false,
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--single-process",
    ],
  });
  const context = await browser.newContext({
    viewport: VIEWPORT,
    deviceScaleFactor: 1,
  });

  const styleEntries = Object.entries(STYLES);
  let completed = 0;
  const total = styleEntries.length * PAGES.length;

  for (const [styleId, styleDef] of styleEntries) {
    for (const pageType of PAGES) {
      const page = await context.newPage();
      const url = `${baseUrl}?page=${pageType}`;

      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 10000 });

      // Inject style tokens
      await applyStyle(page, styleId, styleDef.vars);

      // Allow fonts and repaints to settle
      await page.waitForTimeout(500);

      const filename = `${styleId}-${pageType}.png`;
      const filepath = join(OUTPUT_DIR, filename);

      await page.screenshot({
        path: filepath,
        fullPage: false,
        clip: { x: 0, y: 0, width: VIEWPORT.width, height: VIEWPORT.height },
      });

      completed++;
      console.log(
        `[${completed}/${total}] ${styleDef.name} / ${pageType} -> ${filename}`
      );

      await page.close();
    }
  }

  await context.close();
  await browser.close();
  server.close();

  console.log(`\nDone! ${completed} screenshots saved to ${OUTPUT_DIR}`);
}

main().catch((err) => {
  console.error("Screenshot generation failed:", err);
  process.exit(1);
});

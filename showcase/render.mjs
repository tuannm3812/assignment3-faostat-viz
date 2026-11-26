// Render showcase HTML to PDF and PNG with Playwright's Chromium.
// Usage: node showcase/render.mjs slides|poster <file.html> <outDir>
import { createRequire } from 'module';
import path from 'path';
import { pathToFileURL } from 'url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const [kind, src, outDir] = process.argv.slice(2);
const url = pathToFileURL(path.resolve(src)).href;
const browser = await chromium.launch();

if (kind === 'slides') {
  // 960 x 540 pt = 1280 x 720 CSS px; scale 1.5 gives 1920 x 1080 PNGs.
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5 });
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: path.join(outDir, 'slides.pdf'), preferCSSPageSize: true, printBackground: true });
  const slides = await page.$$('section.slide');
  for (let i = 0; i < slides.length; i++) {
    await slides[i].screenshot({ path: path.join(outDir, `slide-${i + 1}.png`) });
  }
} else {
  // A1 landscape: 841 x 594 mm = 3178.6 x 2245 CSS px; scale to 6000 px wide.
  const w = Math.round(841 / 25.4 * 96), h = Math.round(594 / 25.4 * 96);
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 6000 / w });
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: path.join(outDir, 'poster-landscape.pdf'), preferCSSPageSize: true, printBackground: true });
  await page.screenshot({ path: path.join(outDir, 'poster-landscape.png'), clip: { x: 0, y: 0, width: w, height: h } });
}
await browser.close();

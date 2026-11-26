// Render each story-*.html card in a folder to a 2x PNG with Playwright's Chromium.
// Usage: node showcase/render_cards.mjs <dir> <width> <height>
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const [dir, w, h] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2 });
for (const f of fs.readdirSync(dir).filter((f) => /^story-.*\.html$/.test(f)).sort()) {
  await page.goto(pathToFileURL(path.resolve(dir, f)).href);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(dir, f.replace('.html', '.png')), clip: { x: 0, y: 0, width: +w, height: +h } });
}
await browser.close();

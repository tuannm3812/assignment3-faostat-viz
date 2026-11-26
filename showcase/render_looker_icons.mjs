// Render the Looker dashboard icons (Lucide, ISC licence) as 96px PNGs. Needs lucide-static@0.460.0 in node_modules.
import { createRequire } from 'module'; import fs from 'fs';
const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const out = '/home/user/assignment3-faostat-viz/showcase/output/looker/icons';
const svg = n => fs.readFileSync(`node_modules/lucide-static/icons/${n}.svg`, 'utf8').replace(/<!--[\s\S]*?-->/g,'');
// [file, icon, colour, badge]
const set = [
 ['card-price','trending-up','#3B528B',1],['card-peak','mountain','#3B528B',1],['card-exposed','globe','#440154',1],
 ['card-signal','bell','#1B2430',1],['card-record','circle-check','#21918C',1],
 ['col-filters','sliders-horizontal','#5A6370',0],['col-read','book-open','#5A6370',0],['col-warning','bell','#5A6370',0],['col-sources','database','#5A6370',0],
 ['panel-shock','trending-up','#3B528B',1],['panel-exposure','globe','#440154',1],['panel-warning','bell','#B8452E',1],
];
const b = await chromium.launch(); const p = await b.newPage({ viewport:{width:96,height:96}, deviceScaleFactor:1 });
for (const [f,n,c,badge] of set) {
  const s = svg(n).replace(/stroke="currentColor"/,`stroke="${c}"`).replace(/width="24"/,'width="%W"').replace(/height="24"/,'height="%W"').replace(/stroke-width="2"/,'stroke-width="2"');
  const w = badge ? 52 : 80;
  const bg = badge ? `background:${c}1F;border-radius:50%;` : '';
  await p.setContent(`<html><body style="margin:0;background:transparent"><div style="width:96px;height:96px;display:flex;align-items:center;justify-content:center;${bg}">${s.replaceAll('%W',w)}</div></body></html>`);
  await p.screenshot({ path:`${out}/${f}.png`, omitBackground:true });
}
await b.close(); console.log('done');

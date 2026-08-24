// 用 Playwright 錄製 index.html，輸出 webm（無音訊）
// 之後 ffmpeg 再 mux 旁白總軌（見檔尾印出的指令）
//
// 執行方式（Playwright 刻意裝在非雲端硬碟路徑，見 GOTCHAS D-1 / D-2）：
//   PowerShell:  $env:NODE_PATH = "$env:TEMP\avs-render\node_modules"; node record.cjs
//   Bash:        NODE_PATH="$TEMP/avs-render/node_modules" node record.cjs
// 沒裝過先跑：bash ../../install/setup_playwright.sh

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  console.error('找不到 playwright。先跑 install/setup_playwright.sh，');
  console.error('再設 NODE_PATH 指向 %TEMP%/avs-render/node_modules（見 GOTCHAS D-2）。');
  process.exit(1);
}
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'],
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: { dir: path.join(__dirname, 'renders'), size: { width: 1920, height: 1080 } },
  });
  const page = await context.newPage();

  // ?render=true → 頁面隱藏點擊遮罩且不自動開播，等這支腳本喊開始（GOTCHAS D-3）
  const fileUrl = 'file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/') + '?render=true';
  console.log('Loading:', fileUrl);
  await page.goto(fileUrl);

  // 等字型就緒才開播，否則前幾頁會用預設字型
  await page.evaluate(() => document.fonts.ready);

  // 片長直接取自頁面的 PAGES，改旁白稿不必回來改這支腳本
  const total = await page.evaluate(() => window.__totalDur);
  if (!total) throw new Error('讀不到 window.__totalDur，確認 index.html 尾端有匯出');
  const ms = total * 1000 + 1500; // +1.5s 讓最後一頁的退場動畫走完
  console.log(`Recording ${total}s (+1.5s buffer)...`);

  await page.evaluate(() => window.__startShow());
  await page.waitForTimeout(ms);

  await context.close();
  await browser.close();
  console.log('Done → renders/*.webm');
  console.log('');
  console.log('接著合成旁白（-map 不能省，見 GOTCHAS E-2）：');
  console.log('  ffmpeg -y -i renders/<檔名>.webm -i assets/narration/master.mp3 \\');
  console.log('    -map 0:v:0 -map 1:a:0 \\');
  console.log('    -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest final.mp4');
})();

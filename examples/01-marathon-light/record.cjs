// 用 Playwright 錄製 index.html，輸出 webm（無音訊）
// 之後 ffmpeg 再 mux 音樂（見檔尾印出的指令）
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

  // 等字型就緒才開播，否則開頭幾拍會用預設字型
  await page.evaluate(() => document.fonts.ready);

  // 片長直接取自頁面的 TOTAL，改長度不必回來改這支腳本
  // 中止時要把 Playwright 已經開始寫的那段 webm 一起刪掉：recordVideo 是在 context
  // 建立當下就開錄的，直接 close 會讓半截廢片落地，後面 ls renders/*.webm 就會抓到兩個。
  async function abort(lines) {
    const video = page.video();
    await context.close();
    if (video) await video.delete().catch(() => {});
    await browser.close();
    lines.forEach(l => console.error(l));
    process.exit(1);
  }

  // 分階動畫守衛（GOTCHAS C-7）：dur 要容得下該頁宣告的 anim + 1.5s 消化時間。
  // 只認頁面自己宣告的 anim，不做靜態分析——推斷會漏（非 .slide-N 選擇器上的
  // transition、任意控制流的 setTimeout 都抓不到），宣告不會。
  const tooShort = await page.evaluate(() => (window.__pages || [])
    .map(p => ({ i: p.i, dur: p.dur != null ? p.dur : (p.e - p.s), anim: p.anim }))
    .filter(p => p.anim && p.dur < p.anim + 1.5));
  if (tooShort.length) {
    await abort([
      '這幾頁的 dur 容不下宣告的分階動畫（需 anim + 1.5s，見 GOTCHAS C-7）：',
      ...tooShort.map(p =>
        `  page ${p.i}: dur ${p.dur}s < anim ${p.anim}s + 1.5s = ${(p.anim + 1.5).toFixed(1)}s`),
      '請加長 index.html 的 dur，或把動畫節奏調快後同步改 anim。',
    ]);
  }

  const total = await page.evaluate(() => window.__totalDur);
  if (!total) throw new Error('讀不到 window.__totalDur，確認 index.html 尾端有匯出');
  const ms = total * 1000 + 1500; // +1.5s 讓最後一拍走完
  console.log(`Recording ${total}s (+1.5s buffer)...`);

  await page.evaluate(() => window.__startShow());

  // 本範本的時間軸是由 audio.currentTime 驅動的：沒有音檔就整支不會動，
  // 會靜靜錄出一段黑畫面。先確認音軌真的在跑，比事後看廢片好查。
  await page.waitForTimeout(600);
  const t = await page.evaluate(() => document.getElementById('audio').currentTime);
  if (!t) {
    await abort([
      '音訊沒有前進（currentTime = 0）。本範本不含 binary，',
      '請先把 BGM 放到 assets/audio/ 並對應 index.html 的 <audio src>。',
    ]);
  }

  await page.waitForTimeout(ms - 600);

  await context.close();
  await browser.close();
  console.log('Done → renders/*.webm');
  console.log('');
  console.log('接著合成音樂（-map 不能省，見 GOTCHAS E-2）：');
  console.log('  ffmpeg -y -i renders/<檔名>.webm -i assets/audio/<你的BGM>.mp3 \\');
  console.log('    -map 0:v:0 -map 1:a:0 \\');
  console.log('    -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest final.mp4');
})();

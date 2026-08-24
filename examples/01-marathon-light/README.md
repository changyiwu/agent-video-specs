# 01 — marathon-light（活動紀錄影片範本）

**規範**：[../../specs/01-活動紀錄影片.md](../../specs/01-活動紀錄影片.md)

**這是範本，不含 binary**。Fork 後依規範自行準備：
- 10 張劇情圖（Unsplash / draw 技能 / 自己拍）
- BGM mp3
- 各場景字卡與旁白文案

## 檔案

- `index.html` — 10 場景 HTML 動畫骨架（SOIL 字卡、Ken Burns、進度條、淡出）
- `DESIGN.md` — 設計規範（配色、字體、鏡頭）
- `SCRIPT.md` — 旁白與字卡逐 beat 規劃範本
- `record.cjs` — Playwright 錄製腳本（片長自動取自 `TOTAL`）

## Fork 後動工

1. 編輯 `SCRIPT.md` 替換成你的故事
2. 編輯 `index.html` 內的 PAGES 與 `assets/images/` 對應檔名
3. 準備音檔放 `assets/audio/`
4. 先裝 Playwright：`bash ../../install/setup_playwright.sh`（裝在 %TEMP%，不要裝進雲端硬碟）
5. 錄製：`NODE_PATH="$TEMP/avs-render/node_modules" node record.cjs` → `renders/*.webm`
   （Windows PowerShell 的寫法見 `record.cjs` 檔頭註解）
6. 合成音樂：`record.cjs` 跑完會印出可直接複製的 ffmpeg 指令，另見 [規範第 8 章](../../specs/01-活動紀錄影片.md)

> `record.cjs` 用 `?render=true` 載入頁面，跳過「點擊播放」遮罩，片長自動從 `TOTAL` 讀取，
> 所以你改片長不必回頭改這支腳本。
> 本範本的時間軸由 `audio.currentTime` 驅動——**沒放 BGM 就整支不會動**，
> `record.cjs` 會在 0.6 秒內偵測到並中止，不會讓你白等一趟黑畫面。

完整流程參見根目錄 [BOOTSTRAP.md](../../BOOTSTRAP.md) 階段 3。

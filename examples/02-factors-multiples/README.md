# 02 — factors-multiples（教學影片範本）

**規範**：[../../specs/02-教學影片.md](../../specs/02-教學影片.md)

**這是範本，不含 binary**。Fork 後依規範自行準備：
- 14 段 Edge-TTS 旁白（跑 `python generate_narration.py`）
- 字體（跑 `bash ../../install/install_fonts.sh`）

## 檔案

- `index.html` — 14 頁教學動畫骨架（KaTeX、SVG 因數樹、知識地圖）
- `generate_narration.py` — Edge-TTS 序列生成 14 段旁白
- `record.cjs` — Playwright 錄製腳本（片長自動取自 `PAGES`）

## Fork 後動工

1. 跑字體安裝：`bash ../../install/install_fonts.sh`
2. 修改 `generate_narration.py` 內的 SCRIPT 陣列為你的內容
3. 跑 `python generate_narration.py` 生成 `assets/narration/page-*.mp3`
4. 修改 `index.html` 內的 PAGES、SVG、字卡為你的科目
5. 用 ffprobe 確認旁白時長 → 對應到 `PAGES.dur`；有分階動畫的頁一併宣告 `PAGES.anim`
   （`python generate_narration.py` 會印出稽核表，不合規會中止並且不產出 master.mp3）
6. 先裝 Playwright：`bash ../../install/setup_playwright.sh`（裝在 %TEMP%，不要裝進雲端硬碟）
7. 錄製：`NODE_PATH="$TEMP/avs-render/node_modules" node record.cjs` → `renders/*.webm`
   （Windows PowerShell 的寫法見 `record.cjs` 檔頭註解）
8. 合成旁白：`record.cjs` 跑完會印出可直接複製的 ffmpeg 指令

> `record.cjs` 用 `?render=true` 載入頁面，跳過「點擊播放」遮罩，片長自動從 `PAGES` 加總，
> 所以你改旁白稿、增減頁數都不必回頭改這支腳本。

> 改動畫節奏時記得同步改 `PAGES` 的 `anim`（該頁分階動畫跑完的秒數）。
> `dur` 必須 ≥ `anim + 1.5s`，`generate_narration.py` 與 `record.cjs` 會各擋一道（GOTCHAS C-7）。

完整流程參見根目錄 [BOOTSTRAP.md](../../BOOTSTRAP.md) 階段 3，或 [規範第 10 章 checklist](../../specs/02-教學影片.md)。

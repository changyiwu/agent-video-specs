# 03 — ai-context（社群科普影片範本）

**規範**：[../../specs/03-社群科普影片.md](../../specs/03-社群科普影片.md)

**這是範本，不含 binary**。Fork 後依規範自行準備：
- 12 段 Edge-TTS 旁白
- 3 張 Unsplash 照片（或依你的主題替換）
- 字體（跑 `bash ../../install/install_fonts.sh`）

## 檔案

- `index.html` — 12 頁多版面動畫骨架（6 種版面 L1–L6 全用上）
- `generate_narration.py` — Edge-TTS 序列生成 12 段旁白
- `record.cjs` — Playwright 錄製腳本（片長自動取自 `PAGES`）

## Fork 後動工

1. 跑字體安裝：`bash ../../install/install_fonts.sh`
2. 修改 `generate_narration.py` 內的 SCRIPT 為你的科普內容
3. `python generate_narration.py`
4. 用 WebFetch 找 3 張 Unsplash 照片 ID，`curl` 下載到 `assets/images/`
5. 修改 `index.html` 內的 PAGES、SVG、版面對應你的主題；有分階動畫的頁宣告 `PAGES.anim`
   （`python generate_narration.py` 會印出稽核表，不合規會中止並且不產出 master.mp3）
6. 先裝 Playwright：`bash ../../install/setup_playwright.sh`（裝在 %TEMP%，不要裝進雲端硬碟）
7. 錄製：`NODE_PATH="$TEMP/avs-render/node_modules" node record.cjs` → `renders/*.webm`
   （Windows PowerShell 的寫法見 `record.cjs` 檔頭註解）
8. 合成旁白：`record.cjs` 跑完會印出可直接複製的 ffmpeg 指令

> `record.cjs` 用 `?render=true` 載入頁面，跳過「點擊播放」遮罩，片長自動從 `PAGES` 加總，
> 所以你改旁白稿、增減頁數都不必回頭改這支腳本。

## 預設使用的 Unsplash 照片（可替換）

| 用途 | Unsplash ID |
|------|-------------|
| 便利貼 | `photo-1580934174026-8142803ebb5b` |
| 圖書館 | `photo-1743207820696-6ea16d63177f` |
| 辦公室 | `photo-1518455027359-f3f8164ba6bd` |

> 改動畫節奏時記得同步改 `PAGES` 的 `anim`（該頁分階動畫跑完的秒數）。
> `dur` 必須 ≥ `anim + 1.5s`，`generate_narration.py` 與 `record.cjs` 會各擋一道（GOTCHAS C-7）。

完整流程參見根目錄 [BOOTSTRAP.md](../../BOOTSTRAP.md) 階段 3，或 [規範第 11 章 checklist](../../specs/03-社群科普影片.md)。

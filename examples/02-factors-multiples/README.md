# 02 — factors-multiples（教學影片範本）

**規範**：[../../specs/02-教學影片.md](../../specs/02-教學影片.md)

**這是範本，不含 binary**。Fork 後依規範自行準備：
- 14 段旁白（跑 `python generate_narration.py`，預設 Edge-TTS）
- 字體（跑 `bash ../../install/install_fonts.sh`，會複製進本資料夾的 `assets/fonts/`）

## 檔案

- `index.html` — HyperFrames composition：14 頁教學動畫（KaTeX、SVG 因數樹、知識地圖），所有動畫在同一條 GSAP 時間軸上
- `generate_narration.py` — 逐頁生成旁白 + 稽核時間軸（`--tts kokoro` 可改用 HyperFrames 內建 TTS）

## Fork 後動工

1. 第一次用先備環境：`bash ../../install/setup_hyperframes.sh`、`bash ../../install/install_fonts.sh`
2. 修改 `generate_narration.py` 內的 SCRIPT 陣列為你的內容
3. 跑 `python generate_narration.py` 生成 `assets/narration/page-*.mp3`，並印出「旁白 vs 版面」稽核表
4. 修改 `index.html` 的頁面、SVG、字幕為你的科目；依稽核表調每頁的 `data-start`／`data-duration`
   （規則寫在 `index.html` 的 `#root` 上方註解。只改頁長時跑 `python generate_narration.py --audit`，不必重跑 TTS）
5. 預覽：`npx hyperframes preview`（瀏覽器開啟，存檔自動重新整理）
6. 關卡：`npx hyperframes check`，必須顯示 `Check passed`
7. 出片：`npx hyperframes render -o final.mp4`（1920×1080、30fps，旁白自動混音）

> **頁長的兩個下限都有機制擋**（GOTCHAS C-7）：
> - 旁白比頁長還長 → `generate_narration.py` 直接 `exit 1`
> - 分階動畫跑完後不到 1.5 秒就換頁 → `index.html` 檔尾的守衛會丟錯，`check` 判定失敗
>
> 守衛直接量時間軸上每個 tween 的結束時間，不需要人工宣告動畫長度。
> 刻意持續到頁尾的裝飾動畫（粒子、∞ 脈動、進度條）要加 `data: 'ambient'`，教學 reveal 不要加。

> KaTeX 的樣式由檔尾的 `loadCss()` 在執行期載入，載完才註冊時間軸。
> 不要改回 `<link rel="stylesheet">`，算繪出來的公式會重複兩次（GOTCHAS D-6）。

完整流程參見根目錄 [BOOTSTRAP.md](../../BOOTSTRAP.md) 階段 3，或 [規範第 10 章 checklist](../../specs/02-教學影片.md)。

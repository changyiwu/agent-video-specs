# 03 — ai-context（社群科普影片範本）

**規範**：[../../specs/03-社群科普影片.md](../../specs/03-社群科普影片.md)

**這是範本，不含 binary**。Fork 後依規範自行準備：
- 12 段旁白（跑 `python generate_narration.py`，預設 Edge-TTS）
- 3 張 Unsplash 照片（或依你的主題替換）
- 字體（跑 `bash ../../install/install_fonts.sh`，會複製進本資料夾的 `assets/fonts/`）

## 檔案

- `index.html` — HyperFrames composition：12 頁多版面動畫（6 種版面 L1–L6 全用上），所有動畫在同一條 GSAP 時間軸上
- `generate_narration.py` — 逐頁生成旁白 + 稽核時間軸（`--tts kokoro` 可改用 HyperFrames 內建 TTS）

## Fork 後動工

1. 第一次用先備環境：`bash ../../install/setup_hyperframes.sh`、`bash ../../install/install_fonts.sh`
2. 修改 `generate_narration.py` 內的 SCRIPT 為你的科普內容
3. 跑 `python generate_narration.py`，看「旁白 vs 版面」稽核表
4. 用 WebFetch 找 3 張 Unsplash 照片 ID，`curl` 下載到 `assets/images/`（檔名見下表）
5. 修改 `index.html` 的頁面、SVG、版面對應你的主題；依稽核表調每頁的 `data-start`／`data-duration`
   （`.anim` 元素的 `data-d` 是頁內毫秒延遲。只改頁長時跑 `python generate_narration.py --audit`）
6. 預覽：`npx hyperframes preview`
7. 關卡：`npx hyperframes check`，必須顯示 `Check passed`（照片沒下載會在這裡報 404）
8. 出片：`npx hyperframes render -o final.mp4`

## 預設使用的 Unsplash 照片（可替換）

| 用途 | 檔名 | Unsplash ID |
|------|------|-------------|
| 便利貼（第 2 頁） | `assets/images/sticky-notes.jpg` | `photo-1580934174026-8142803ebb5b` |
| 辦公室（第 7 頁） | `assets/images/office.jpg` | `photo-1518455027359-f3f8164ba6bd` |
| 圖書館（第 9 頁） | `assets/images/library.jpg` | `photo-1743207820696-6ea16d63177f` |

> **頁長的兩個下限都有機制擋**（GOTCHAS C-7）：旁白比頁長還長時 `generate_narration.py` 會 `exit 1`；
> `.anim` 排得太晚、跑完後不到 1.5 秒就換頁時，`index.html` 檔尾的守衛會丟錯，`check` 判定失敗。
> 守衛直接量時間軸，不需要人工宣告動畫長度。

完整流程參見根目錄 [BOOTSTRAP.md](../../BOOTSTRAP.md) 階段 3，或 [規範第 11 章 checklist](../../specs/03-社群科普影片.md)。

# 01 — marathon-light（活動紀錄影片範本）

**規範**：[../../specs/01-活動紀錄影片.md](../../specs/01-活動紀錄影片.md)

**這是範本，不含 binary**。Fork 後依規範自行準備：
- 10 張劇情圖（Unsplash / draw 技能 / 自己拍）→ `assets/images/`
- BGM mp3 → `assets/audio/`
- 各場景字卡與旁白文案

## 檔案

- `index.html` — HyperFrames composition：10 拍 × 5 秒（SOIL 字卡、Ken Burns、交叉淡化、進度條、BGM 淡出）
- `DESIGN.md` — 設計規範（配色、字體、鏡頭）
- `SCRIPT.md` — 旁白與字卡逐 beat 規劃範本

## Fork 後動工

1. 第一次用先備環境：`bash ../../install/setup_hyperframes.sh`
2. 編輯 `SCRIPT.md` 替換成你的故事
3. 編輯 `index.html` 的每一拍（`<section class="beat">`）：圖檔名、章節、字卡、字幕
4. 準備 BGM 放 `assets/audio/`，改 `<audio id="bgm">` 的 `src`
5. 改片長時，同步改每拍的 `data-start`／`data-duration`、根節點與 BGM 的 `data-duration`（規則寫在 `#root` 上方註解）
6. 預覽：`npx --yes hyperframes@0.8.171 preview`
7. 關卡：`npx --yes hyperframes@0.8.171 check`，必須顯示 `Check passed`
8. 出片：`npx --yes hyperframes@0.8.171 render --quality high -o final.mp4`

> **缺素材會被 `check` 擋下**（GOTCHAS E-3）：沒放 BGM 時 lint 報 `audio_src_not_found`，
> 圖片缺檔時 runtime 報 404。`render` 本身不會擋缺圖，所以 `check` 不能省（GOTCHAS D-8）。

> 每拍的 clip 比拍長多 0.8 秒，和下一拍重疊做交叉淡化；文字會在下一拍進場前 1 秒先收掉，
> 交叉淡化只疊畫面、不疊字（兩拍字卡疊在一起時 `check` 會報 `content_overlap`）。
> BGM 最後 5 秒淡出用 `data-fade-out`；之後若加旁白，用 `data-automation` 做 ducking（規範第 6 節）。

完整流程參見根目錄 [BOOTSTRAP.md](../../BOOTSTRAP.md) 階段 3。

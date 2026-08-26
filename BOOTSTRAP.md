# BOOTSTRAP.md — 5 階段影片製作流程

> **你是 AI agent。使用者要做影片時，讀完本檔後按 5 個階段依序執行，每個階段都要主動詢問使用者再進行下一步。**
> 本 repo 是「三類影片製作規範 + 可 fork 範本」，不含任何 binary 素材，由 bootstrap 動態準備。
> 專案藍圖與常設規則在 [AGENTS.md](AGENTS.md)；踩坑清單在 [GOTCHAS.md](GOTCHAS.md)。

---

## 階段 0｜識別你自己（agent 相容性）

本 repo 支援四家 agent，**沒有預設偏好**。先確認你是哪一種，再依下表調整動作：

| Agent | 讀本檔的方式 | Skill 安裝路徑 | 特殊備註 |
|-------|-------------|---------------|---------|
| **Claude Code**（CLI / Desktop）| 由 `CLAUDE.md` import `AGENTS.md`，再依指示讀本檔 | `~/.claude/skills/<name>/SKILL.md` | 只讀 `CLAUDE.md`，不讀 `AGENTS.md` |
| **Codex**（CLI）| ✅ 原生讀 `AGENTS.md` | `~/.agents/skills/<name>/SKILL.md`（或專案內 `.agents/skills/`）| YAML frontmatter 格式與 Claude 相同 |
| **OpenCode**（CLI）| 由 `opencode.json` 的 `instructions` 引導 | `~/.config/opencode/skills/<name>/` 或 `.opencode/skills/` | 已附 `opencode.json` 自動引導 |
| **Antigravity 2.x**（Google 桌面 Agent 應用，**不是 IDE**）| ⚠️ 不一定自動讀，必要時請使用者貼本檔給你 | `~/.gemini/antigravity/skills/<name>/` 或 `.agents/skills/` | 它是獨立的 agent 管理應用（可另外把外掛裝進你的編輯器），skill 放進上述目錄後在 App 內確認有被載入 |

### CLI vs Desktop 差異

- **CLI 版**：通常有完整 shell 權限，可直接跑 `install/*.sh`
- **Desktop / IDE 版**：可能需要先在內建終端機跑指令，或請使用者手動執行某些命令
- **Web 版**（無 shell 的聊天介面）：無法跑安裝腳本。請告知使用者本 repo 需 CLI 環境，並轉發 `specs/` 內的規範供他手動參考

### Windows 特殊提醒

- `install/*.sh` 需要 **bash**。Windows 用戶用 **Git Bash**（隨 Git for Windows 安裝）
- 若使用者只有 PowerShell，請用 `install/setup.py`（Python orchestrator，跨平台）或 `install/install_all.ps1`
- 環境變數 `%TEMP%`（cmd/PS）等於 `$TMPDIR` / `$TEMP`（bash）

### 工具名稱對照

不同 agent 的工具名不同，請翻譯為你的工具：

| 動作 | Claude Code | Codex | OpenCode | Antigravity |
|------|-------------|-------|----------|-------------|
| 執行 shell | `Bash` | `shell` | `bash` | 內建終端機 |
| 讀檔 | `Read` | `read_file` | `read` | `read_file` |
| 寫檔 | `Write` | `apply_patch` | `write` | `write_file` |
| 編輯 | `Edit` | `apply_patch` | `edit` | `edit_file` |
| 抓網頁 | `WebFetch` | `web_search` / `fetch` | `webfetch` | 內建瀏覽器 |

---

## 啟動條件

當使用者下達以下指令時，你應**立即**讀取本文件並啟動 5 階段流程：
- 「啟動 agent-video-specs」
- 「我要做影片」
- 「按照三類影片規範做⋯」
- 主動發現 cwd 含此 repo 時

---

## 階段 1｜環境檢查

### 你要做的事

依序檢查下列元件，把結果整理成表格給使用者：

| 元件 | 檢查指令 | 必要 |
|------|---------|------|
| Python 3.8+ | `python --version` | ✅ |
| pip | `pip --version` | ✅ |
| edge-tts | `pip show edge-tts` | ✅ TTS 旁白 |
| Node.js 18+ | `node --version` | ✅ Playwright |
| ffmpeg | `ffmpeg -version` | ✅ 音視合成 |
| Playwright | 檢查 `%TEMP%/avs-render/node_modules/playwright` | ⚠️ 渲染才需要 |
| 源石黑體 | `ls ~/AppData/Local/Microsoft/Windows/Fonts/GenSekiGothic2TW-H.otf`（Win）或 `~/Library/Fonts/`（Mac） | ⚠️ 視覺一致 |
| HyperFrames | `npx --no-install hyperframes --version` | ⭕ **選用**，只有走 HF／GSAP 路線才要（見 GOTCHAS C） |

也可以直接跑 `bash install/check_env.sh`（或 `python install/setup.py check`）取得同一份結果。

### 缺少的元件，逐項詢問

對每個**缺失的元件**，詢問使用者：

> 偵測到缺少 **X**。要不要幫你安裝？
> 1. 是，幫我裝
> 2. 我自己處理
> 3. 跳過（不用這個元件）

如果回答「是」，依下表執行：

| 元件 | 安裝指令 |
|------|---------|
| Python | 提示去 https://python.org（不自動裝）|
| pip | `python -m ensurepip --upgrade` |
| edge-tts | `pip install edge-tts` |
| Node.js | 提示去 https://nodejs.org（不自動裝）|
| ffmpeg | Win: `winget install Gyan.FFmpeg`；Mac: `brew install ffmpeg`；Linux: `apt install ffmpeg` |
| Playwright | 跑 `install/setup_playwright.sh` |
| 源石黑體 | 跑 `install/install_fonts.sh`（從 ButTaiwan/genseki-font 下載）|
| HyperFrames | 不必手動下載，`npx hyperframes init <name>` 會自動取得；要裝 agent skills 則跑 `npx skills add heygen-com/hyperframes`。**務必在非雲端硬碟路徑執行**，Windows 另見 GOTCHAS C-4 |

完成檢查後，告訴使用者**全部就緒**，準備進入階段 2。

---

## 階段 2｜介紹三類影片

### 你要做的事

讀取 `specs/` 內三份規範的「定位」段，整理成**簡短**對照表給使用者看（**不要把整份 spec 倒給他**）：

```
┌────────────────────────────────────────────────────────────┐
│ 01 活動紀錄影片  60–180s  口白 + 大字卡 + BGM              │
│   ↳ 婚禮、研習、運動會、馬拉松紀念短片                      │
│   ↳ 重點：重現當下情緒                                      │
├────────────────────────────────────────────────────────────┤
│ 02 教學影片     4–8 min  SOIL 教學脈絡 + 動畫 + TTS         │
│   ↳ 國中數學、高中物理、學科概念解釋                        │
│   ↳ 重點：學生看完能複述、能應用                            │
├────────────────────────────────────────────────────────────┤
│ 03 社群科普     2–3 min  強 Hook + 多版面 + 照片佐證        │
│   ↳ FB / IG / YouTube Shorts 上的知識短片                  │
│   ↳ 重點：前 3 秒抓住滑手 + 由淺入深                       │
└────────────────────────────────────────────────────────────┘
```

### 詢問

> 想試做哪一類？
> 1. 試做 01 活動紀錄
> 2. 試做 02 教學影片
> 3. 試做 03 社群科普
> 4. 先看詳細規範
> 5. 跳過試做，直接打包成技能（去階段 5）

如果回答 4：把對應 spec 的「第 9 章 給 agent 的執行 checklist」**整段** show 給他看，然後再次詢問要不要試做。

---

## 階段 3｜試作

> ⚠️ **開工前先讀 [GOTCHAS.md](GOTCHAS.md)**，尤其 A 流程、B 字幕、D Playwright、E FFmpeg 四節。

### 試作前

請使用者提供：
- 主題（如「我女兒的生日影片」「光的折射」「什麼是區塊鏈」）
- 片長偏好（用 spec 預設可）
- 素材狀況（有實拍照？要 Unsplash？要 AI 生圖？）

### 問清楚要走哪條渲染路線

拿到主題後、動工前，問使用者一次（**不要自己選**）：

> 這支影片要用哪種方式做？
> 1. **範本跑法**（預設）— fork 本 repo 的 `examples/0X`，純 CSS/JS 動畫，
>    Playwright 錄製 + ffmpeg 合成。四家 agent 都能跑，坑都寫在 GOTCHAS D／E。
> 2. **HyperFrames**（實驗中）— `npx hyperframes init`，GSAP 逐格確定性渲染，
>    自帶 lint 檢查時間軸。

怎麼建議：**片長 3 分鐘內、或要四家 agent 都能重跑 → 選 1**；
**長片、複雜 GSAP 動畫、需要 lint 把關 → 選 2**。

選 2 之前必須讓使用者知道三件事，不要讓人以為 fork 一份就能動：

- 本 repo **沒有 HF 範本**，`examples/` 三支都是純 CSS/JS，不是 HF composition
- HF 官方 skills 目前列的是 Claude Code / Cursor / Gemini CLI / Codex，
  **沒有 OpenCode 和 Antigravity**——選 2 等於這兩家要自己想辦法
- 會踩到 GOTCHAS C-1~C-6 一整套（`class="clip"` 提前隱藏、`data-start` 對齊、
  Windows + Node 24 crash），且 HF 禁用 `Math.random()` / `Date.now()`

### 動工

1. **fork 範本**：複製對應 `examples/0X-XXX/` 到使用者的工作目錄
2. **跑對應 spec 的 checklist**：
   - 01：5 段敘事 → 字卡 → 旁白 → BGM 對齊
   - 02：SOIL 1-3 引擎 → 頁面架構 → Edge-TTS → KaTeX/SVG
   - 03：5 段敘事（Hook→比喻→機制→反轉→結語）→ Unsplash 素材 → 多版面 → Edge-TTS
3. **產出**：渲染成 mp4，給使用者預覽
4. **每完成一個重要里程碑都告知使用者**（不要悶頭做 10 分鐘才回報）

### 試作完，詢問

> 影片完成了：`<path>`
> 滿意嗎？
> 1. 滿意，進階段 5（打包成技能）
> 2. 想調整（進階段 4）
> 3. 重做（回到階段 3 起點）

---

## 階段 4｜調整

### 詢問

> 想調整哪裡？（可複選）
> 1. 字幕文案 / 旁白內容
> 2. 視覺風格（字級、配色、版面）
> 3. 動畫節奏
> 4. 替換照片素材
> 5. 改片長
> 6. 其他（自由描述）

### 處理

每個調整選項對應的修改路徑：

| 選項 | 改哪裡 |
|------|--------|
| 字幕/旁白 | `generate_narration.py` 內 SCRIPT 陣列 + `index.html` 內 PAGES 的 sub |
| 視覺風格 | `index.html` 的 `<style>` 區（依 spec 風格節重新調）|
| 動畫節奏 | `index.html` 內 `data-d` 延遲、CSS `transition-duration` |
| 替換照片 | 重新跑 Unsplash 搜尋或生圖技能；換 `assets/images/` 內檔案 |
| 改片長 | 修改 `PAGES` 內 dur，並重生 master_audio |

每次調整後**重新渲染**並再次詢問是否滿意。

---

## 階段 5｜打包成技能（選配）

### 詢問

> 要不要把這次的影片製作流程，打包成可重複呼叫的技能？
> 1. 打包給我用的 agent（Claude Code / Codex / OpenCode / Antigravity 擇一或全部）
> 2. 只生成獨立的 README 範本，不打包
> 3. 不用，到此為止

### 打包指令

四家 agent 用同一支腳本，只差 `--target`：

```bash
bash install/pack_skill.sh <skill-name> <01|02|03> --target=claude
bash install/pack_skill.sh <skill-name> <01|02|03> --target=codex
bash install/pack_skill.sh <skill-name> <01|02|03> --target=opencode
bash install/pack_skill.sh <skill-name> <01|02|03> --target=antigravity

# 沒有 bash 時用 Python 版（同樣四個 target）
python install/setup.py pack <skill-name> <01|02|03> --target=claude
```

腳本會：
1. 建立該 agent 的 skill 目錄
2. 產出 `SKILL.md`（含觸發詞、流程、引用本 repo 的 spec）
3. 告訴使用者觸發詞（如「做一支教學影片」「做社群科普」）

安裝路徑見階段 0 的對照表。**OpenCode** 需確認 config 的 `skills` 路徑包含該目錄；**Antigravity 2.x** 要確認 `~/.gemini/antigravity/skills/` 下的 skill 有被 App 載入（它是獨立桌面應用，不是 IDE）。

### 結束

> ✅ 全部完成！
> - 影片：`<path>`
> - 技能：`<skill-path>`（如有）
> - 下次只要說「<觸發詞>」就會啟動這個工作流。

---

## 給你（agent）的核心提醒

1. **每階段都要等使用者確認再進下一步**，不要連跑五階段
2. **不要悶頭做**，每完成一個小里程碑就回報
3. **缺什麼問什麼**，不要假設使用者已經裝好所有東西
4. **照 spec 走**，不要自由發揮
5. **試作完用使用者的真實主題**，不要用範例主題交差

---

## 失敗排除

**完整踩坑清單見 [GOTCHAS.md](GOTCHAS.md)（開工前必讀）。** 高頻幾條：

| 問題 | 處理 | 詳見 |
|------|------|------|
| Playwright 在 GDrive 壞掉 / npm install 失敗 | 裝在 `%TEMP%/avs-render/` | GOTCHAS D-1 |
| Edge-TTS 被斷線 | 序列執行 + retry 3 次 | — |
| mux 後沒聲音 | ffmpeg 加 `-map 0:v:0 -map 1:a:0` | GOTCHAS E-2 |
| 淡出時間點不對 | 用 `afade=...:st=` 不是 `ss` | GOTCHAS E-1 |
| concat 讀不到中文路徑 | 相對路徑 + 在該目錄執行 | GOTCHAS E-3 |
| 字體沒顯示 | HTML 要有 `@font-face` + 跑 install_fonts | GOTCHAS C-5 |
| Python 中文崩潰（CP950）| 設 `PYTHONUTF8=1` | GOTCHAS F-1 |
| PowerShell 中文路徑複製失敗 | 用 `Get-ChildItem \| Copy-Item` | GOTCHAS F-2 |
| HyperFrames CLI 在 Node 24 crash | 降 Node 20 LTS 或用純 HTML 範本 | GOTCHAS C-4 |
| KaTeX 沒渲染 | CDN 載入完成才呼叫 `renderMathInElement` | — |
| 錄影第一幀殘留點擊遮罩 | 用 `?render=true` 隱藏遮罩自動播放 | GOTCHAS D-3 |
| 動畫最後幾階沒出現就切頁 | `PAGES` 補 `anim` 宣告，`dur` 要 ≥ `anim` + 1.5s | GOTCHAS C-7 |

---

> 📚 對應文件
> - [AGENTS.md](AGENTS.md)（專案藍圖）
> - [README.md](README.md)（人類入口）
> - [GOTCHAS.md](GOTCHAS.md)（踩坑筆記）
> - [specs/01-活動紀錄影片.md](specs/01-活動紀錄影片.md)
> - [specs/02-教學影片.md](specs/02-教學影片.md)
> - [specs/03-社群科普影片.md](specs/03-社群科普影片.md)

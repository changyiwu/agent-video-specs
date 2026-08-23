@AGENTS.md

<!--
  本檔是「橋接檔」：Claude Code 只讀 CLAUDE.md，不讀 AGENTS.md，
  所以用第一行的 @AGENTS.md 把跨 Agent 專案藍圖 import 進來。
  專案內容一律寫進 AGENTS.md，這裡只放 Claude Code 專屬規範，避免兩份分叉。
-->

## Claude Code 專屬

- 本專案支援四家 agent 且**刻意不以 Claude 為預設**。回應與文件不要寫成「這是 Claude 專用的 repo」，也不要把 Claude Code 的路徑／工具名當成通則寫進 `AGENTS.md`、`BOOTSTRAP.md`、`README.md` 或 `install/` 腳本——那四處要維持四家對等。
- 打包技能測試時，別只跑 `--target=claude`；四個 target 都要驗過再說「打包功能正常」。
- `examples/03-ai-context/` 的影片內容有提到 Claude 與 `/compact`，那是**影片主題本身**（在講 context window），不是品牌綁定，去識別化時不要動它。

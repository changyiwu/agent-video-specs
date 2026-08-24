#!/usr/bin/env bash
# 把影片製作流程打包成目標 agent 的 skill
# 用法：bash install/pack_skill.sh <skill-name> <video-type 01|02|03> [--target claude|codex|opencode|antigravity|all]
# --target 省略時預設 all（四家 agent 全裝），本 repo 對四家 agent 對等支援。
set -e

NAME="${1:-video-maker}"
TYPE="${2:-02}"
TARGET="all"
for arg in "$@"; do
  case "$arg" in
    --target=*) TARGET="${arg#--target=}" ;;
  esac
done

case "$TYPE" in
  01) TITLE="活動紀錄影片"; TRIGGER="做一支活動紀錄/婚禮/研習/比賽影片" ;;
  02) TITLE="教學影片";     TRIGGER="做一支教學影片/學科解釋影片" ;;
  03) TITLE="社群科普影片"; TRIGGER="做一支社群科普/IG/YouTube Shorts 短片" ;;
  *)  echo "Type 必須是 01 / 02 / 03"; exit 1 ;;
esac

REPO_ROOT="$(dirname "$(dirname "$(realpath "$0")")")"

ALL_TARGETS="claude codex opencode antigravity"
case "$TARGET" in
  all) TARGETS="$ALL_TARGETS" ;;
  claude|codex|opencode|antigravity) TARGETS="$TARGET" ;;
  *) echo "Target 必須是 claude / codex / opencode / antigravity / all"; exit 1 ;;
esac

# 各 agent 的 skill 安裝根目錄（單一真相來源見 BOOTSTRAP.md 階段 0）
skill_root() {
  case "$1" in
    claude)      echo "$HOME/.claude/skills" ;;
    codex)       echo "$HOME/.agents/skills" ;;
    opencode)    echo "$HOME/.config/opencode/skills" ;;
    antigravity) echo "$HOME/.gemini/antigravity/skills" ;;
  esac
}

for t in $TARGETS; do
  SKILL_DIR="$(skill_root "$t")/$NAME"
  META_FILE="$SKILL_DIR/SKILL.md"
  mkdir -p "$SKILL_DIR"

  cat > "$META_FILE" <<EOF
---
name: $NAME
description: 依 agent-video-specs 第 $TYPE 類規範製作 $TITLE
target: $t
---

# $TITLE 生成技能（$NAME）

## 用途
依照 agent-video-specs 第 $TYPE 類規範製作 $TITLE。

## 觸發情境
使用者說：
- 「$TRIGGER」
- 「按照規範做一支 $TITLE」
- 「跑 $NAME 工作流」

## 工作流
1. 確認主題、片長、素材狀況
2. **先讀踩坑筆記**：\`$REPO_ROOT/GOTCHAS.md\`（A 流程 / B 字幕 / D Playwright / E FFmpeg）
3. 讀規範：\`$REPO_ROOT/specs/$TYPE-*.md\`
4. **產出 SCRIPT.md 與 DESIGN.md 給使用者確認後才動工**（GOTCHAS A-3，不可跳過）
5. fork 範本：複製 \`$REPO_ROOT/examples/$TYPE-*/\` 到工作目錄
6. 跑該 spec 第 9 / 11 章 checklist
7. Edge-TTS 序列生成旁白
8. Playwright（裝在 %TEMP%/avs-render/）錄製 webm
9. ffmpeg mux master_audio → mp4（必加 \`-map 0:v:0 -map 1:a:0\`）
10. 給使用者預覽 → 確認後存檔

## 規範路徑
\`$REPO_ROOT/specs/$TYPE-*.md\`

## 範本路徑
\`$REPO_ROOT/examples/$TYPE-*/\`

## 完整流程
\`$REPO_ROOT/BOOTSTRAP.md\`（5 階段）

## 主要工具
- Edge-TTS（zh-TW-YunJheNeural）
- KaTeX（數學）
- Playwright + ffmpeg（渲染）
- 源石黑體（執行 \`bash $REPO_ROOT/install/install_fonts.sh\` 安裝）

## 注意事項
- Playwright node_modules 必須在 %TEMP%/avs-render/，不能放雲端硬碟
- Edge-TTS 並行會被斷線，序列 + retry 3 次
- 字幕單行 ≤ 25 字，不換行
- 字體引用相對路徑為 \`../../assets/fonts/\`（fork 後路徑依位置調整）
EOF

  echo "✓ $t → $SKILL_DIR"

  case "$t" in
    opencode)
      echo "    ℹ️  OpenCode 額外需要：在你的 opencode.json 或 .opencode/config.json 內"
      echo "        確認 \"skills\" 路徑包含 ~/.config/opencode/skills/"
      ;;
    antigravity)
      echo "    ℹ️  Antigravity 2.x 是獨立桌面 Agent 應用（不是 IDE）"
      echo "        請在 App 內確認 ~/.gemini/antigravity/skills/ 的 skill 已被載入"
      echo "        若無自動偵測，請手動將 $META_FILE 內容貼入 Antigravity 的 Custom Agent 設定"
      ;;
  esac
done

echo ""
echo "  技能名稱 : $NAME（第 $TYPE 類・$TITLE）"
echo "  觸發詞   : 「$TRIGGER」"

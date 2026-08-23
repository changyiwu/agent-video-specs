#!/usr/bin/env bash
# 從 ButTaiwan/genseki-font 下載源石黑體 H/B/M 三個字重
# 用法：bash install/install_fonts.sh
set -e

UPSTREAM="https://github.com/ButTaiwan/genseki-font/raw/master/otf/TW"
WANT=("GenSekiGothic2TW-H.otf" "GenSekiGothic2TW-B.otf" "GenSekiGothic2TW-M.otf")

# 決定安裝目標
case "$(uname -s)" in
  MINGW*|CYGWIN*|MSYS*)  TARGET="$HOME/AppData/Local/Microsoft/Windows/Fonts" ;;
  Darwin*)               TARGET="$HOME/Library/Fonts" ;;
  Linux*)                TARGET="$HOME/.local/share/fonts" ;;
  *)                     TARGET="$HOME/.fonts" ;;
esac
mkdir -p "$TARGET"

echo "→ 安裝目標：$TARGET"
for f in "${WANT[@]}"; do
  if [ -f "$TARGET/$f" ]; then
    echo "✓ 已存在 $f"
  else
    echo "↓ 下載 $f"
    # -f 不可省：沒有它時 404 會把 GitHub 的 HTML 錯誤頁寫成 .otf，要到渲染階段才會發現字體壞掉
    if ! curl -fsSL -o "$TARGET/$f" "$UPSTREAM/$f"; then
      rm -f "$TARGET/$f"
      echo "✗ 下載失敗：$UPSTREAM/$f" >&2
      echo "  上游 repo 可能改過目錄結構，請確認 UPSTREAM 路徑" >&2
      exit 1
    fi
  fi
done

# 同步一份到 repo 本地 assets/fonts/（讓範例 HTML 引用）
REPO_FONTS="$(dirname "$(dirname "$(realpath "$0")")")/assets/fonts"
mkdir -p "$REPO_FONTS"
for f in "${WANT[@]}"; do
  cp -n "$TARGET/$f" "$REPO_FONTS/" 2>/dev/null || true
done

echo "✓ 完成。系統字體：$TARGET、Repo 副本：$REPO_FONTS"
echo "  Linux 用戶請執行 fc-cache -fv 重新整理"

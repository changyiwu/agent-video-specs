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

# 同步一份到 repo 的 assets/fonts/，再複製進每個範本的 assets/fonts/：
# HyperFrames 不接受 ../ 跳出專案根目錄的字型路徑，每個影片專案都要有自己的一份（GOTCHAS D-2）
REPO="$(dirname "$(dirname "$(realpath "$0")")")"
for dir in "$REPO" "$REPO"/examples/*; do
  mkdir -p "$dir/assets/fonts"
  for f in "${WANT[@]}"; do
    cp -n "$TARGET/$f" "$dir/assets/fonts/" 2>/dev/null || true
  done
done

echo "✓ 完成。系統字體：$TARGET；專案副本：$REPO/assets/fonts 與 examples/*/assets/fonts"
echo "  fork 範本到別處時，連同 assets/fonts/ 一起複製"
echo "  Linux 用戶請執行 fc-cache -fv 重新整理"

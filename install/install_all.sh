#!/usr/bin/env bash
# 一鍵安裝所有 optional 元件（前提：python、node、ffmpeg 已存在）
# 用法：bash install/install_all.sh
set -e

DIR="$(dirname "$(realpath "$0")")"

echo "1️⃣  安裝 Edge-TTS 與 tools/ 用到的套件（字型瘦身、照片套色）"
pip install --quiet edge-tts fonttools brotli pillow pypinyin opencc-python-reimplemented || pip3 install --quiet edge-tts fonttools brotli pillow pypinyin opencc-python-reimplemented

echo "2️⃣  下載源石黑體"
bash "$DIR/install_fonts.sh"

echo "3️⃣  準備 HyperFrames（含算繪用 Chrome）"
bash "$DIR/setup_hyperframes.sh"

echo ""
echo "✅ 全部就緒。可以進入階段 2（試做影片）了"

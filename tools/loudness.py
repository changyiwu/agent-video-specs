# 量測成片響度，並正規化到 −14 LUFS（YouTube 與各社群平台的播放基準）、真峰值 ≤ −1 dBTP
# 執行（在 repo 根目錄）：
#   python tools/loudness.py videos/<主題>/final.mp4            只量測
#   python tools/loudness.py videos/<主題>/final.mp4 --apply    正規化後覆蓋原檔（-o 另存）
#
# 規範在 GOTCHAS E-6：每支片 render 完都要跑 --apply，再交片。HyperFrames 的 `normalize-audio`
# 只調單一音軌的 data-volume（旁白對 BGM 的相對音量），管不到整支片混音後的響度，所以要在成片上做。
# 做法是 ffmpeg loudnorm 兩段式：第一段量測，第二段帶入量測值做線性增益（不壓縮動態），
# 視訊串流直接複製、不重新編碼，只重編音訊（AAC 192k）。已經在目標 ±0.5 LU 內就不動。
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

TARGET_I, TARGET_TP, TARGET_LRA = -14.0, -1.0, 11.0
TOLERANCE = 0.5


def ffmpeg(args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg 失敗：\n{r.stderr[-2000:]}")
    return r.stderr


def loudnorm_json(stderr):
    # loudnorm 把結果印成 stderr 最後一個 JSON 區塊
    blocks = re.findall(r"\{[^{}]*\}", stderr)
    if not blocks:
        raise SystemExit("ffmpeg 沒有印出 loudnorm 結果（檔案有音軌嗎？）")
    return json.loads(blocks[-1])


def measure(path):
    af = f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json"
    return loudnorm_json(ffmpeg(["-i", str(path), "-map", "0:a:0", "-af", af, "-f", "null", "-"]))


def show(label, m):
    print(f"{label}：整合響度 {float(m['input_i']):6.1f} LUFS　真峰值 {float(m['input_tp']):5.1f} dBTP"
          f"　響度範圍 {float(m['input_lra']):4.1f} LU")


def main():
    ap = argparse.ArgumentParser(description="成片響度量測與正規化（−14 LUFS／−1 dBTP）")
    ap.add_argument("video", help="成片（通常是 videos/<主題>/final.mp4）")
    ap.add_argument("--apply", action="store_true", help="正規化（預設覆蓋原檔）")
    ap.add_argument("-o", "--output", help="正規化結果另存到這裡，不覆蓋原檔")
    a = ap.parse_args()
    src = Path(a.video).resolve()
    if not src.exists():
        raise SystemExit(f"找不到 {src}")

    m = measure(src)
    show("目前", m)
    off_i = float(m["input_i"]) - TARGET_I
    ok = abs(off_i) <= TOLERANCE and float(m["input_tp"]) <= TARGET_TP
    print(f"目標：{TARGET_I:g} LUFS ±{TOLERANCE:g}、真峰值 ≤ {TARGET_TP:g} dBTP → {'符合' if ok else '不符合'}")
    if not a.apply:
        if not ok:
            print(f"要正規化：python tools/loudness.py \"{a.video}\" --apply")
        return
    if ok:
        print("已在目標範圍內，不改檔")
        return

    dest = Path(a.output).resolve() if a.output else src
    tmp = dest.with_name(dest.stem + ".loudnorm-tmp" + dest.suffix)
    af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
          f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
    err = ffmpeg(["-y", "-i", str(src), "-map", "0:v?", "-map", "0:a:0", "-c:v", "copy",
                  "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(tmp)])
    kind = loudnorm_json(err).get("normalization_type", "?")
    os.replace(tmp, dest)
    show("處理後", measure(dest))
    if kind != "linear":
        # 線性增益會讓峰值超過 −1 dBTP 時，loudnorm 會改用動態壓縮：響度對了，但動態被壓過
        print("注意：這次 loudnorm 用的是動態模式（線性增益會讓峰值破表），聽一下有沒有被壓扁的感覺")
    print(f"→ {dest}")


if __name__ == "__main__":
    main()

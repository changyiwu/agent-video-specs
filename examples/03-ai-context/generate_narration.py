import asyncio, edge_tts
import re
import subprocess
import sys
from pathlib import Path

# Windows 主控台預設 CP950，直接 print 中文會變亂碼。
# 下面「旁白 vs 版面」對照表正是要靠它判斷哪頁該調 dur，印成亂碼等於白印。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).parent / "assets" / "narration"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "zh-TW-YunJheNeural"
RATE = "-8%"
PITCH = "-2Hz"

SCRIPT = [
    (1,  "為什麼 AI 用一用，會突然忘了你剛剛說過什麼？"),
    (2,  "AI 沒有真正的記憶。它有的，是一張短期便利貼。這張便利貼，叫做「上下文」。"),
    (3,  "你說的每句話、AI 回的每句話，都會被一起貼在這張便利貼上。AI 才有辦法接話。"),
    (4,  "便利貼的單位叫做 token，大約一個中文字就是一個 token。GPT-4 約十二萬八千 token，Claude 約二十萬。聽起來很多——"),
    (5,  "但對話越長，越早的內容會被擠出視窗。AI 就「忘了」前面講過什麼。"),
    (6,  "所以，不是 AI 變笨。是它的便利貼被塞爆了。"),
    (7,  "怎麼辦？這裡有三個破解的招式。"),
    (8,  "第一招：摘要。把舊對話濃縮成重點，省下空間。Claude Code 裡的 compact 指令，就是這個。"),
    (9,  "第二招：外部記憶。把資訊存到檔案或資料庫，要用時再撈回來。這叫做 RAG。"),
    (10, "第三招：分工。讓子代理處理細節，主代理只接收結果摘要。避免每個 agent 都拿到全部 context。"),
    (11, "三個馬上能用的小建議：開新對話、適時 compact、長文件交給 agent 從檔案讀。"),
    (12, "AI 的智力，受限於它能記得多少。學會管理上下文，就是學會放大它的腦容量。"),
]

async def synth(i, text):
    out = OUT / f"page-{i:02d}.mp3"
    c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await c.save(str(out))
    print(f"OK page-{i:02d}.mp3")

async def main():
    for i, t in SCRIPT:
        for r in range(3):
            try:
                await synth(i, t); break
            except Exception as e:
                print(f"retry {i} ({r+1}): {e}")
                await asyncio.sleep(2)
    print("All done.")

# ---- 以下把 12 段分軌組成一條 master.mp3，供 record.cjs 之後 mux ----
# 分軌不能直接串接：每頁的旁白都比版面短，要按各頁起點擺放，中間留白。


def page_specs():
    """從 index.html 的 PAGES 逐頁讀 dur 與 anim——版面長度以 index.html 為單一真相來源。

    anim 是該頁分階動畫跑完的秒數，由頁面自己宣告（沒有分階 reveal 的頁不會有）。
    這裡不做靜態分析去猜動畫多長：推斷會漏（宣告在非 .slide-N 選擇器上的 transition、
    任意控制流的 setTimeout 都抓不到），宣告不會。見 GOTCHAS C-7。
    """
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
    block = re.search(r"const PAGES = \[(.*?)\n\];", html, re.S)
    if not block:
        raise SystemExit("index.html 找不到 const PAGES，無法決定每頁長度")
    specs = []
    for line in block.group(1).splitlines():
        m = re.search(r"dur:\s*(\d+)", line)
        if not m:
            continue
        a = re.search(r"anim:\s*([\d.]+)", line)
        specs.append((int(m.group(1)), float(a.group(1)) if a else None))
    if len(specs) != len(SCRIPT):
        raise SystemExit(f"PAGES 有 {len(specs)} 頁，SCRIPT 有 {len(SCRIPT)} 段，兩者要一致")
    return specs


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def audit(specs, starts):
    """對每頁檢查 dur 的兩個下限，回傳 (errors, warns)。

    錯誤（會做出壞影片，直接中止）：旁白比版面長、或 dur 容不下宣告的動畫。
    警告（規範建議值，不中止）：tail 落在 2~4s 之外。
    """
    errors, warns = [], []
    print("\n旁白 vs 版面（dur 下限：旁白 + 2~4s，且 動畫 + 1.5s——見 GOTCHAS C-7）：")
    for (i, _), (d, anim), s in zip(SCRIPT, specs, starts):
        a = probe(OUT / f"page-{i:02d}.mp3")
        tail = d - a
        marks = []
        if a > d:
            errors.append(f"page {i:02d}：旁白 {a:.2f}s 比版面 {d}s 長，尾巴會被切掉")
            marks.append("旁白超出版面")
        elif tail < 2:
            warns.append(f"page {i:02d}：tail 只有 {tail:.2f}s（規範建議 2~4s）")
            marks.append("tail 偏短")
        elif tail > 4:
            warns.append(f"page {i:02d}：tail 有 {tail:.2f}s（規範建議 2~4s）")
            marks.append("tail 偏長")
        if anim is not None and d < anim + 1.5:
            errors.append(
                f"page {i:02d}：dur {d}s 容不下動畫 {anim}s + 1.5s = {anim + 1.5:.1f}s，動畫會被切掉")
            marks.append("動畫被切掉")
        shown = f"{anim:5.1f}s" if anim is not None else "    —"
        note = "  <== " + "、".join(marks) if marks else ""
        print(f"  page {i:02d}  旁白 {a:6.2f}s  版面 {d:3d}s  餘裕 {tail:5.2f}s  動畫 {shown}{note}")
    return errors, warns


def build_master():
    specs = page_specs()
    starts, t = [], 0
    for d, _ in specs:
        starts.append(t)
        t += d

    errors, warns = audit(specs, starts)
    for w in warns:
        print(f"  警告：{w}")
    if errors:
        print()
        for e in errors:
            print(f"  錯誤：{e}")
        raise SystemExit("\n版面長度不合規，先改 index.html 的 dur／anim 再重跑（master.mp3 未產出）")

    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for i, _ in SCRIPT:
        args += ["-i", str(OUT / f"page-{i:02d}.mp3")]
    delays = ";".join(f"[{n}]adelay={s * 1000}|{s * 1000}[a{n}]" for n, s in enumerate(starts))
    mixin = "".join(f"[a{n}]" for n in range(len(SCRIPT)))
    # apad 不可省：最後一段唸完就沒聲音了，master 會短於版面總長，
    # mux 時 -shortest 會連帶把影片尾巴一起截掉。
    args += ["-filter_complex",
             f"{delays};{mixin}amix=inputs={len(SCRIPT)}:normalize=0:dropout_transition=0,apad[out]",
             "-map", "[out]", "-t", str(t), "-c:a", "libmp3lame", "-q:a", "2",
             str(OUT / "master.mp3")]
    subprocess.run(args, check=True)
    print(f"\nOK master.mp3  {probe(OUT / 'master.mp3'):.2f}s（版面總長 {t}s）")


if __name__ == "__main__":
    asyncio.run(main())
    build_master()

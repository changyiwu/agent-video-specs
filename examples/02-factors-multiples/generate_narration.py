# 用 Edge-TTS 生成 14 段旁白
# 執行：python generate_narration.py
import asyncio
import re
import subprocess
import edge_tts
from pathlib import Path

import sys

# Windows 主控台預設 CP950，直接 print 中文會變亂碼。
# 下面「旁白 vs 版面」對照表正是要靠它判斷哪頁該調 dur，印成亂碼等於白印。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT = Path(__file__).parent / "assets" / "narration"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "zh-TW-YunJheNeural"
RATE = "-10%"
PITCH = "-2Hz"

SCRIPT = [
    (1,  "因數與倍數。國中數學最基礎、也最常被誤會的單元。今天我們用六分鐘，把它徹底搞懂。"),
    (2,  "二十四個人，要分組。可以分成兩組，每組十二人；三組，每組八人；四組，每組六人。為什麼是這幾種？因為這些數字，剛好能把二十四整除。能整除的數字，就是二十四的——因數。"),
    (3,  "整除是什麼？一個數除以另一個數，餘數是零，就叫整除。二十四除以六等於四，餘零。所以我們說：六整除二十四。"),
    (4,  "因數的定義：如果 a 乘上某個整數等於 b，那 a 就是 b 的因數。二十四等於六乘四，所以六和四，都是二十四的因數。"),
    (5,  "怎麼找十二的所有因數？用配對法。一乘十二、二乘六、三乘四。三組配對，六個因數：一、二、三、四、六、十二。"),
    (6,  "注意，因數的個數是有限的。十二的因數，永遠只有這六個，不會再多。這是因數的第一個重要特性：有限。"),
    (7,  "倍數呢？反過來。五的倍數，就是五乘一、五乘二、五乘三⋯⋯ 五、十、十五、二十⋯⋯ 無止盡地往下延伸。"),
    (8,  "倍數的個數，是無限的。一條數線往右拉，永遠拉不到底。因數有限，倍數無限——這是因數與倍數最大的不同。"),
    (9,  "在所有正整數裡，有一種特別的數，它的因數只有兩個：一、和它自己。這種數，叫做質數。二、三、五、七、十一⋯⋯ 都是質數。"),
    (10, "除了一和質數以外，剩下的正整數都叫合數。合數的特色是——可以被拆解。十二可以拆成二乘六，六又可以拆成二乘三。一直拆到不能再拆，全部都是質數。"),
    (11, "這就是因數樹。從六十開始：六十等於二乘三十。三十等於二乘十五。十五等於三乘五。樹的末端，全部都是質數：二、二、三、五。把它們乘回去，就還原成六十。這個過程，叫做質因數分解。"),
    (12, "今天學了四件事：整除性、因數、倍數、以及質數合數。它們其實是同一件事的不同看法。"),
    (13, "拆到底，是質數。擴出去，是倍數。"),
    (14, "下次遇到一個數字，試著問自己：它能被誰整除？又能被誰拆解？這就是因數與倍數的全部。"),
]

async def synth(i, text):
    out = OUT / f"page-{i:02d}.mp3"
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(str(out))
    print(f"OK page-{i:02d}.mp3")

async def main():
    for i, t in SCRIPT:
        for attempt in range(3):
            try:
                await synth(i, t)
                break
            except Exception as e:
                print(f"retry {i} ({attempt+1}): {e}")
                await asyncio.sleep(2)
    print("All done.")


# ---- 以下把 14 段分軌組成一條 master.mp3，供 record.cjs 之後 mux ----
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

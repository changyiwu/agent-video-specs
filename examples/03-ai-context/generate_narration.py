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

def page_durs():
    """從 index.html 的 PAGES 讀每頁秒數——版面長度以 index.html 為單一真相來源。"""
    html = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
    block = re.search(r"const PAGES = \[(.*?)\n\];", html, re.S)
    if not block:
        raise SystemExit("index.html 找不到 const PAGES，無法決定每頁長度")
    durs = [int(d) for d in re.findall(r"dur:\s*(\d+)", block.group(1))]
    if len(durs) != len(SCRIPT):
        raise SystemExit(f"PAGES 有 {len(durs)} 頁，SCRIPT 有 {len(SCRIPT)} 段，兩者要一致")
    return durs


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def build_master():
    durs = page_durs()
    starts, t = [], 0
    for d in durs:
        starts.append(t)
        t += d

    print("\n旁白 vs 版面：")
    over = []
    for (i, _), d, s in zip(SCRIPT, durs, starts):
        a = probe(OUT / f"page-{i:02d}.mp3")
        mark = ""
        if a > d:
            over.append(i)
            mark = "  <== 旁白比版面長，會被切掉"
        print(f"  page {i:02d}  旁白 {a:6.2f}s  版面 {d:3d}s  餘裕 {d - a:5.2f}s{mark}")
    if over:
        print(f"  警告：第 {over} 頁需要加長 index.html 的 dur，或把旁白講短一點")

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

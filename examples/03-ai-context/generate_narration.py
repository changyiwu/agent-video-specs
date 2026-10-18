# 生成 12 段逐頁旁白，並稽核 index.html 的時間軸
# 執行：
#   python generate_narration.py               生成旁白（Edge-TTS）+ 稽核
#   python generate_narration.py --audit       只稽核（改了 data-duration 之後用，不重跑 TTS）
#   python generate_narration.py --tts kokoro  改用 HyperFrames 內建 TTS（Kokoro，中國腔，見 specs/02 7.1）
# 稽核通過後：npx hyperframes check → npx hyperframes render -o final.mp4
import argparse
import asyncio
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

# Windows 主控台預設 CP950，直接 print 中文會變亂碼。
# 下面「旁白 vs 版面」對照表正是要靠它判斷哪頁該調 data-duration，印成亂碼等於白印。
# SystemExit 的訊息走 stderr，兩條都要改。
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
OUT = HERE / "assets" / "narration"

# Edge-TTS（預設，台灣腔）
VOICE = "zh-TW-YunJheNeural"
RATE = "-8%"  # 社群片比教學片略快（specs/03）
PITCH = "-2Hz"

# HyperFrames 內建 Kokoro-82M（備案：免網路、免金鑰，但只有中國口音的 zf_xiaobei）
KOKORO_VOICE = "zf_xiaobei"
KOKORO_SPEED = 0.92  # 對應 Edge-TTS 的 RATE -8%

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


# ---- TTS ----

async def synth_edge(i, text):
    import edge_tts
    c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await c.save(str(OUT / f"page-{i:02d}.mp3"))


def synth_kokoro(i, text):
    npx = shutil.which("npx")
    if not npx:
        raise SystemExit("找不到 npx，先跑 install/setup_hyperframes.sh（需要 Node.js 22+）")
    with tempfile.TemporaryDirectory() as tmp:
        # 旁白文字走 .txt 檔，不直接當參數傳：Windows 的 npx 是 .cmd，
        # 中文標點與 & | ^ 之類字元經過 cmd.exe 轉義會壞掉
        txt, wav = Path(tmp) / "line.txt", Path(tmp) / "line.wav"
        txt.write_text(text, encoding="utf-8")
        subprocess.run([npx, "--yes", "hyperframes", "tts", str(txt), "--voice", KOKORO_VOICE,
                        "--speed", str(KOKORO_SPEED), "--output", str(wav)], check=True)
        # 轉成 mp3：index.html 的 <audio src> 一律指向 page-NN.mp3，換引擎不必改版面
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-c:a", "libmp3lame", "-q:a", "2", str(OUT / f"page-{i:02d}.mp3")], check=True)


async def generate(engine):
    OUT.mkdir(parents=True, exist_ok=True)
    for i, t in SCRIPT:
        for attempt in range(3):
            try:
                if engine == "kokoro":
                    synth_kokoro(i, t)
                else:
                    await synth_edge(i, t)
                print(f"OK page-{i:02d}.mp3")
                break
            except Exception as e:
                print(f"retry {i} ({attempt + 1}): {e}")
                await asyncio.sleep(2)
        else:
            raise SystemExit(f"page-{i:02d} 連續三次生成失敗")
    print("All done.")


# ---- 稽核：index.html 的時間軸 ----
# 時間軸的唯一真相來源是 index.html 標籤上的 data-start／data-duration（HyperFrames 靜態讀取，
# 見 GOTCHAS D-3）。這裡檢查它和旁白對不對得上，不合規就 exit 1，不要進 render。

class Timeline(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root_dur = None
        self.pages = []   # (page, id, start, dur)
        self.audios = {}  # id -> (src, start, dur)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "data-composition-id" in a and self.root_dur is None:
            self.root_dur = float(a["data-duration"]) if "data-duration" in a else None
        if "data-page" in a:
            self.pages.append((int(a["data-page"]), a.get("id"),
                               float(a.get("data-start", "nan")), float(a.get("data-duration", "nan"))))
        if tag == "audio" and a.get("id"):
            self.audios[a["id"]] = (a.get("src"), float(a.get("data-start", "nan")),
                                    float(a.get("data-duration", "nan")))


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def audit():
    tl = Timeline()
    tl.feed((HERE / "index.html").read_text(encoding="utf-8"))
    pages = sorted(tl.pages)
    errors, warns = [], []

    if len(pages) != len(SCRIPT):
        raise SystemExit(f"index.html 有 {len(pages)} 頁（data-page），SCRIPT 有 {len(SCRIPT)} 段，兩者要一致")

    # 1. 起點連續：每頁 start = 前一頁 start + duration
    expect = 0.0
    for n, pid, start, dur in pages:
        if start != expect:
            errors.append(f"page {n:02d}（#{pid}）data-start={start:g}，應為 {expect:g}（前一頁 start + duration）")
        expect = start + dur
    total = sum(d for *_, d in pages)

    # 2. 根節點總長 = 各頁加總
    if tl.root_dur != total:
        errors.append(f"根節點 data-duration={tl.root_dur}，應為各頁加總 {total:g}")

    # 3. 每頁的旁白 <audio> 要和該頁同時段
    for n, _, start, dur in pages:
        aid = f"nar-{n:02d}"
        if aid not in tl.audios:
            errors.append(f"page {n:02d}：找不到 <audio id=\"{aid}\">（沒有 id 的 audio 會被混音器略過）")
            continue
        src, a_start, a_dur = tl.audios[aid]
        if src != f"assets/narration/page-{n:02d}.mp3":
            errors.append(f"page {n:02d}：#{aid} 的 src 是 {src}，應為 assets/narration/page-{n:02d}.mp3")
        if (a_start, a_dur) != (start, dur):
            errors.append(f"page {n:02d}：#{aid} 時段 {a_start:g}+{a_dur:g}s 和頁面 {start:g}+{dur:g}s 不一致")

    # 4. 旁白 vs 版面：dur >= 旁白 + 2~4s（動畫 + 1.5s 那條下限由頁面自己的守衛量，見 GOTCHAS C-7）
    print("\n旁白 vs 版面（data-duration 下限：旁白 + 2~4s——見 GOTCHAS C-7）：")
    for n, _, start, dur in pages:
        mp3 = OUT / f"page-{n:02d}.mp3"
        if not mp3.exists():
            errors.append(f"page {n:02d}：缺 {mp3.name}，先跑一次不帶 --audit 的 generate_narration.py")
            continue
        a = probe(mp3)
        tail = dur - a
        mark = ""
        if a > dur:
            errors.append(f"page {n:02d}：旁白 {a:.2f}s 比版面 {dur:g}s 長，尾巴會被切掉")
            mark = "  <== 旁白超出版面"
        elif tail < 2:
            warns.append(f"page {n:02d}：tail 只有 {tail:.2f}s（規範建議 2~4s）")
            mark = "  <== tail 偏短"
        elif tail > 4:
            warns.append(f"page {n:02d}：tail 有 {tail:.2f}s（規範建議 2~4s）")
            mark = "  <== tail 偏長"
        print(f"  page {n:02d}  起點 {start:6g}s  旁白 {a:6.2f}s  版面 {dur:4g}s  餘裕 {tail:5.2f}s{mark}")

    for w in warns:
        print(f"  警告：{w}")
    if errors:
        print()
        for e in errors:
            print(f"  錯誤：{e}")
        raise SystemExit("\n時間軸不合規，先改 index.html 的 data-start／data-duration 再重跑 --audit")
    print(f"\nOK 時間軸稽核通過，總長 {total:g}s。下一步：npx hyperframes check → npx hyperframes render -o final.mp4")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="生成逐頁旁白並稽核 index.html 時間軸")
    ap.add_argument("--audit", action="store_true", help="只稽核，不重跑 TTS")
    ap.add_argument("--tts", choices=["edge", "kokoro"], default="edge",
                    help="edge＝Edge-TTS 台灣腔（預設）；kokoro＝HyperFrames 內建，免網路但為中國口音")
    args = ap.parse_args()
    if not args.audit:
        asyncio.run(generate(args.tts))
    audit()

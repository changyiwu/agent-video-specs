# 生成 14 段逐頁旁白，並稽核 index.html 的時間軸
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
RATE = "-10%"
PITCH = "-2Hz"

# HyperFrames 內建 Kokoro-82M（備案：免網路、免金鑰，但只有中國口音的 zf_xiaobei）
KOKORO_VOICE = "zf_xiaobei"
KOKORO_SPEED = 0.9  # 對應 Edge-TTS 的 RATE -10%

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

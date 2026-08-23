#!/usr/bin/env python3
"""跨平台的 agent-video-specs 安裝 orchestrator。

用法：
  python install/setup.py check       # 環境檢查
  python install/setup.py fonts       # 下載源石黑體
  python install/setup.py playwright  # 裝 Playwright
  python install/setup.py all         # 一次裝完
  python install/setup.py pack <skill-name> <01|02|03> [--target claude|codex|opencode|antigravity|all]
                                      # --target 省略時預設 all（四家 agent 全裝）

不依賴 bash，Windows / macOS / Linux 都能跑。
"""
from __future__ import annotations
import os, sys, shutil, subprocess, urllib.request, platform
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLATFORM = platform.system()  # Windows / Darwin / Linux

FONT_FILES = ["GenSekiGothic2TW-H.otf", "GenSekiGothic2TW-B.otf", "GenSekiGothic2TW-M.otf"]
FONT_UPSTREAM = "https://github.com/ButTaiwan/genseki-font/raw/master/otf/TW"


def font_target_dir() -> Path:
    if PLATFORM == "Windows":
        return Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
    if PLATFORM == "Darwin":
        return Path.home() / "Library" / "Fonts"
    return Path.home() / ".local" / "share" / "fonts"


def temp_dir() -> Path:
    if PLATFORM == "Windows":
        return Path(os.environ.get("TEMP", "C:/Temp"))
    return Path(os.environ.get("TMPDIR", "/tmp"))


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def have_pkg(pkg: str) -> bool:
    return subprocess.call(
        [sys.executable, "-m", "pip", "show", pkg],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ) == 0


def cmd_check():
    rows = [
        ("python", have("python") or have("python3")),
        ("pip", have("pip") or have("pip3")),
        ("edge-tts", have_pkg("edge-tts")),
        ("node", have("node")),
        ("npm", have("npm")),
        ("ffmpeg", have("ffmpeg")),
        ("ffprobe", have("ffprobe")),
        ("fonts", (font_target_dir() / FONT_FILES[0]).exists()),
        ("playwright", (temp_dir() / "avs-render" / "node_modules" / "playwright").exists()),
    ]
    print("=== agent-video-specs 環境檢查 ===")
    for name, ok in rows:
        print(f"{'OK  ' if ok else 'MISS'} {name}")
    missing = [n for n, ok in rows if not ok]
    if missing:
        print(f"\n缺少 {len(missing)} 個：{', '.join(missing)}")
        print("執行 `python install/setup.py all` 一次補齊（不含 python/node/ffmpeg 本身）")
    else:
        print("\n✅ 全部就緒")


def cmd_fonts():
    target = font_target_dir()
    target.mkdir(parents=True, exist_ok=True)
    repo_fonts = REPO / "assets" / "fonts"
    repo_fonts.mkdir(parents=True, exist_ok=True)
    print(f"→ 安裝目標：{target}")
    for f in FONT_FILES:
        dest = target / f
        if dest.exists():
            print(f"  ✓ 已存在 {f}")
        else:
            print(f"  ↓ 下載 {f}")
            url = f"{FONT_UPSTREAM}/{f}"
            try:
                urllib.request.urlretrieve(url, dest)
            except Exception as e:
                dest.unlink(missing_ok=True)
                print(f"  X 下載失敗：{url}")
                print(f"    {e}")
                print("    上游 repo 可能改過目錄結構，請確認 FONT_UPSTREAM 路徑")
                sys.exit(1)
            # 字重檔約 14-17 MB；明顯過小代表拿到的是錯誤頁而不是字型
            if dest.stat().st_size < 1_000_000:
                size = dest.stat().st_size
                dest.unlink(missing_ok=True)
                print(f"  X {f} 只有 {size} bytes，不是字型檔，已刪除")
                sys.exit(1)
        # 同步 repo 副本
        repo_dest = repo_fonts / f
        if not repo_dest.exists():
            shutil.copy(dest, repo_dest)
    print(f"✓ 完成。系統字體：{target}，Repo 副本：{repo_fonts}")
    if PLATFORM == "Linux":
        print("  Linux 用戶請執行 fc-cache -fv 重新整理")


def cmd_playwright():
    work = temp_dir() / "avs-render"
    work.mkdir(parents=True, exist_ok=True)
    if not (work / "package.json").exists():
        subprocess.run(["npm", "init", "-y"], cwd=work, check=True, shell=(PLATFORM == "Windows"))
    if not (work / "node_modules" / "playwright").exists():
        subprocess.run(["npm", "install", "playwright"], cwd=work, check=True, shell=(PLATFORM == "Windows"))
    subprocess.run(["npx", "playwright", "install", "chromium"], cwd=work, check=True, shell=(PLATFORM == "Windows"))
    print(f"✓ Playwright 已安裝於：{work}")


def cmd_install_edge_tts():
    if have_pkg("edge-tts"):
        print("✓ edge-tts 已安裝")
        return
    subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts"], check=True)


def cmd_all():
    print("1/3  安裝 Edge-TTS")
    cmd_install_edge_tts()
    print("\n2/3  下載源石黑體")
    cmd_fonts()
    print("\n3/3  安裝 Playwright")
    cmd_playwright()
    print("\n✅ 全部就緒。可以進入階段 2（試做影片）了")


SKILL_PATHS = {
    "claude":      Path.home() / ".claude" / "skills",
    "codex":       Path.home() / ".agents" / "skills",
    "opencode":    Path.home() / ".config" / "opencode" / "skills",
    "antigravity": Path.home() / ".gemini" / "antigravity" / "skills",
}

TYPE_META = {
    "01": ("活動紀錄影片",   "做一支活動紀錄/婚禮/研習/比賽影片"),
    "02": ("教學影片",       "做一支教學影片/學科解釋影片"),
    "03": ("社群科普影片",   "做一支社群科普/IG/YouTube Shorts 短片"),
}


def cmd_pack(args: list[str]):
    if len(args) < 2:
        print("用法：python install/setup.py pack <skill-name> <01|02|03> "
              "[--target claude|codex|opencode|antigravity|all]")
        print("      --target 省略時預設 all（四家 agent 全裝）")
        sys.exit(1)
    name, vtype = args[0], args[1]
    target = "all"
    for a in args[2:]:
        if a.startswith("--target="):
            target = a.split("=", 1)[1]
    if vtype not in TYPE_META:
        print(f"Type 必須是 01/02/03，收到 {vtype}"); sys.exit(1)
    if target != "all" and target not in SKILL_PATHS:
        print(f"Target 必須是 {list(SKILL_PATHS)} 或 all，收到 {target}"); sys.exit(1)

    targets = list(SKILL_PATHS) if target == "all" else [target]
    title, trigger = TYPE_META[vtype]
    work = temp_dir() / "avs-render"

    for t in targets:
        skill_dir = SKILL_PATHS[t] / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        meta = skill_dir / "SKILL.md"
        meta.write_text(f"""---
name: {name}
description: 依 agent-video-specs 第 {vtype} 類規範製作 {title}
target: {t}
---

# {title} 生成技能（{name}）

## 用途
依照 agent-video-specs 第 {vtype} 類規範製作 {title}。

## 觸發情境
- 「{trigger}」
- 「按照規範做一支 {title}」
- 「跑 {name} 工作流」

## 工作流
1. 確認主題、片長、素材狀況
2. **先讀踩坑筆記**：`{REPO}/GOTCHAS.md`（A 流程 / B 字幕 / D Playwright / E FFmpeg）
3. 讀規範：`{REPO}/specs/{vtype}-*.md`
4. **產出 SCRIPT.md 與 DESIGN.md 給使用者確認後才動工**（GOTCHAS A-3，不可跳過）
5. fork 範本：複製 `{REPO}/examples/{vtype}-*/` 到工作目錄
6. 跑該 spec 第 9 / 11 章 checklist
7. Edge-TTS 序列生成旁白
8. Playwright（{work}）錄製 webm
9. ffmpeg mux master_audio → mp4（必加 `-map 0:v:0 -map 1:a:0`）
10. 給使用者預覽 → 確認後存檔

## 規範路徑
`{REPO}/specs/{vtype}-*.md`

## 範本路徑
`{REPO}/examples/{vtype}-*/`

## 完整流程
`{REPO}/BOOTSTRAP.md`（5 階段）

## 注意
- Playwright node_modules 必須在 `{work}`，不能放雲端硬碟
- Edge-TTS 並行會被斷線，序列 + retry 3 次
- 字幕單行 ≤ 25 字，不換行
""", encoding="utf-8")
        print(f"✓ {t} → {skill_dir}")

    print("")
    print(f"  技能名稱 : {name}（第 {vtype} 類・{title}）")
    print(f"  觸發詞   : 「{trigger}」")


COMMANDS = {
    "check": cmd_check,
    "fonts": cmd_fonts,
    "playwright": cmd_playwright,
    "edge-tts": cmd_install_edge_tts,
    "all": cmd_all,
}


def main(argv: list[str]):
    if len(argv) < 2:
        print(__doc__); sys.exit(0)
    sub = argv[1]
    if sub == "pack":
        cmd_pack(argv[2:])
    elif sub in COMMANDS:
        COMMANDS[sub]()
    else:
        print(f"未知子指令：{sub}\n"); print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)

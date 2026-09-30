"""逐句旁白合成：微软 Edge 神经语音 → 每句 mp3 + 时间表 JSON + SRT。

用法：
    python tts_edge.py narration.json out_dir [--voice zh-CN-YunjianNeural] [--rate +0%] [--gap 0.35]

narration.json 格式（按旁白顺序）：
    {"voice": "zh-CN-YunjianNeural", "rate": "+0%", "pitch": "+0Hz",
     "lines": [{"id": "hook", "text": "预算定下来了。", "voice": "可选覆盖", "rate": "可选覆盖"}]}

产物（out_dir 下）：
    vo-<id>.mp3                 每句音频（Remotion 按句单独 <Audio> 放入 Sequence）
    narration-timing.json       每句实测时长与分词/分句边界（秒），画面时间线以此为准
    narration.srt               以连续排列（句间 gap 秒）生成的参考字幕
依赖：edge-tts（pip install edge-tts==7.2.7）、ffprobe 在 PATH。需要联网。
说明：Edge 在线朗读是非官方接口，适合样片；对外商用请换 Azure Speech 官方服务（同名音色、SSML 兼容）。
"""
import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts


def probe_seconds(path: Path) -> float:
    """用 ffprobe 读取音频实际时长，边界事件的末尾偏移不等于文件时长。"""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


async def synth_line(line: dict, defaults: dict, out_dir: Path) -> dict:
    voice = line.get("voice", defaults["voice"])
    rate = line.get("rate", defaults["rate"])
    pitch = line.get("pitch", defaults["pitch"])
    target = out_dir / f"vo-{line['id']}.mp3"
    communicate = edge_tts.Communicate(line["text"], voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    marks = []
    with target.open("wb") as audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                # offset/duration 单位为 100ns
                marks.append({"text": chunk["text"], "start": chunk["offset"] / 1e7,
                              "end": (chunk["offset"] + chunk["duration"]) / 1e7})
    return {"id": line["id"], "text": line["text"], "voice": voice, "rate": rate,
            "file": target.name, "duration": round(probe_seconds(target), 3), "marks": marks}


def srt_time(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("out_dir")
    ap.add_argument("--voice")
    ap.add_argument("--rate")
    ap.add_argument("--gap", type=float, default=0.35, help="参考 SRT 中句与句的间隔秒数")
    args = ap.parse_args()
    spec = json.loads(Path(args.script).read_text(encoding="utf-8"))
    defaults = {"voice": args.voice or spec.get("voice", "zh-CN-YunjianNeural"),
                "rate": args.rate or spec.get("rate", "+0%"), "pitch": spec.get("pitch", "+0Hz")}
    ids = [line["id"] for line in spec["lines"]]
    if len(set(ids)) != len(ids):
        print("lines[].id 必须唯一", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for line in spec["lines"]:  # 顺序合成，避免在线接口限流
        results.append(await synth_line(line, defaults, out_dir))
        print(f"{line['id']}: {results[-1]['duration']:.2f}s")
    cursor, srt = 0.0, []
    for i, r in enumerate(results, 1):
        r["refStart"] = round(cursor, 3)
        srt.append(f"{i}\n{srt_time(cursor)} --> {srt_time(cursor + r['duration'])}\n{r['text']}\n")
        cursor += r["duration"] + args.gap
    (out_dir / "narration-timing.json").write_text(
        json.dumps({"defaults": defaults, "gap": args.gap, "total": round(cursor - args.gap, 3), "lines": results},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "narration.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"total {cursor - args.gap:.2f}s -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

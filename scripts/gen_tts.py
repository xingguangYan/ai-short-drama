# -*- coding: utf-8 -*-
"""按 vo_EPxx.json 合成台词 mp3，落盘 制作成果/audio/，返回时长供时间轴对位。
用法: python gen_tts.py EP01
"""
import json, os, subprocess, sys, asyncio

ROOT = os.environ.get("DRAMA_ROOT", r"D:\个人资料\网文创作\末日求生_短剧")  # 项目根可用环境变量覆盖

VOICES = {
    "林野": ("zh-CN-YunxiNeural", "+0%", "-2Hz"),
    "苏晚": ("zh-CN-XiaoxiaoNeural", "+0%", "+0Hz"),
    "店员": ("zh-CN-YunjianNeural", "+0%", "-3Hz"),
    "理货员": ("zh-CN-YunjianNeural", "+0%", "-3Hz"),
    "路人甲": ("zh-CN-YunyangNeural", "+0%", "+0Hz"),
    "苗苗": ("zh-CN-XiaoxuanNeural", "+0%", "+0Hz"),
    "女声": ("zh-CN-XiaoxiaoNeural", "+0%", "+0Hz"),
    "女人": ("zh-CN-XiaoxiaoNeural", "+0%", "+0Hz"),
    "老妇": ("zh-CN-XiaoxiaoNeural", "+0%", "-3Hz"),
}

def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0

VO_RATE_BOOST = {"vo": 15, "dialog": 8}

def synth_one(text, voice, rate, pitch, out, vo=False):
    if os.path.exists(out):
        return probe_duration(out)
    boost = VO_RATE_BOOST["vo" if vo else "dialog"]
    base = int(rate.rstrip("%")) if rate.rstrip("%").lstrip("+-").isdigit() else 0
    final_rate = "%+d%%" % (base + boost)
    r = subprocess.run(["edge-tts", "--voice", voice, "--text", text,
                        "--rate=" + final_rate, "--pitch=" + pitch, "--write-media", out],
                       capture_output=True, text=True, encoding="utf-8")
    if not os.path.exists(out) or os.path.getsize(out) < 1000:
        raise RuntimeError("tts failed: " + (r.stderr or "")[-200:])
    return probe_duration(out)

def main():
    ep = sys.argv[1]
    items = json.load(open(os.path.join(ROOT, ".scripts", "vo_%s.json" % ep), encoding="utf-8"))
    adir = os.path.join(ROOT, "剧集", ep, "制作成果", "audio")
    os.makedirs(adir, exist_ok=True)
    lines = []
    for i, it in enumerate(items, 1):
        voice, rate, pitch = VOICES.get(it["who"], ("zh-CN-YunxiNeural", "+0%", "+0Hz"))
        out = os.path.join(adir, "%03d_%s.mp3" % (i, it["who"]))
        dur = synth_one(it["text"], voice, rate, pitch, out, vo=it["vo"])
        lines.append({"idx": i, "scene": it["scene"], "who": it["who"], "text": it["text"],
                      "vo": it["vo"], "file": os.path.basename(out), "dur": round(dur, 2)})
        print("%02d %s %.2fs" % (i, it["who"], dur), flush=True)
    json.dump(lines, open(os.path.join(adir, "voice_list.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("done", len(lines))

if __name__ == "__main__":
    main()

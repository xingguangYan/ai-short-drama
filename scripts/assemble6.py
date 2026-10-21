# -*- coding: utf-8 -*-
"""v6 装配：
- 只保留 H3 镜头自带的人物语音（模型生成、口型同步），不再叠加 TTS
- 不渲染任何底部字幕
- 镜头间直接硬切，无黑场
- 每镜按 EBU 响度归一化到参考片水平（-17.5 LUFS）
用法: python assemble6.py EP01
"""
import json, os, shutil, subprocess, sys

ROOT = os.environ.get("DRAMA_ROOT", r"D:\个人资料\网文创作\末日求生_短剧")  # 项目根可用环境变量覆盖
TARGET_LUFS = -17.5  # 参考片 40359102044-1-16.mp4 实测


def ff(*args):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + (r.stderr or "")[-600:])
    return r


def probe_lufs(path):
    r = ff("ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-")
    for line in r.stderr.splitlines():
        s = line.strip()
        if s.startswith("I:"):
            return float(s.split(":")[1].split()[0])
    return None


def main(ep):
    epdir = os.path.join(ROOT, "剧集", ep, "制作成果")
    vdir = os.path.join(epdir, "videos")
    outdir = os.path.join(epdir, "成片")
    os.makedirs(outdir, exist_ok=True)

    shots = json.load(open(os.path.join(ROOT, ".scripts", "shots_%s.json" % ep), encoding="utf-8"))
    ordered = []
    for s in shots:
        p = os.path.join(vdir, os.path.basename(s["out"]))
        if os.path.exists(p):
            ordered.append(p)
    used = set(ordered)
    for f in sorted(os.listdir(vdir)):
        if f.endswith(".mp4") and os.path.join(vdir, f) not in used:
            ordered.append(os.path.join(vdir, f))
    if not ordered:
        raise RuntimeError("no shots found in " + vdir)

    norm = os.path.join(outdir, "_norm6")
    os.makedirs(norm, exist_ok=True)
    files = []
    for i, p in enumerate(ordered, 1):
        dst = os.path.join(norm, "n%02d.mp4" % i)
        if not os.path.exists(dst):
            lufs = probe_lufs(p)
            gain = 0.0
            if lufs is not None:
                gain = max(-8.0, min(8.0, TARGET_LUFS - lufs))
                print("%s  I=%.1f LUFS -> gain %+.1f dB" % (os.path.basename(p)[:11], lufs, gain), flush=True)
            af = "volume=%.2fdB,alimiter=limit=0.97,aformat=channel_layouts=mono:sample_rates=44100" % gain
            ff("ffmpeg", "-y", "-v", "error", "-i", p,
               "-vf", "scale=1088:1920:flags=lanczos,fps=24", "-af", af,
               "-c:v", "libx264", "-preset", "fast", "-crf", "18",
               "-c:a", "aac", "-b:a", "192k", dst)
        files.append(dst)

    cl = os.path.join(outdir, "_concat6.txt")
    with open(cl, "w", encoding="utf-8") as f:
        for nf in files:
            f.write("file '%s'\n" % nf)
    final = os.path.join(outdir, "%s_成片.mp4" % ep)
    ff("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", cl, "-c", "copy", final)
    os.remove(cl)
    shutil.rmtree(norm, ignore_errors=True)
    dur = ff("ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", final).stdout.strip()
    print("final: %s | %.1fs | %d shots | 保留镜头自带人物语音，无 TTS 无字幕" % (final, float(dur), len(files)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "EP01")

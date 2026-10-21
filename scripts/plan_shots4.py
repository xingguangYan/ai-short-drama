# -*- coding: utf-8 -*-
"""v4.1 分镜规划：一场戏 = 一个长镜头（含该场全部台词，拼接成一段音频做参考）。
台词少的场加环境交代镜。全程人物在场。
"""
import json, os, re, sys

ROOT = os.environ.get("DRAMA_ROOT", r"D:\个人资料\网文创作\末日求生_短剧")  # 项目根可用环境变量覆盖
CHAR_SHEET = {
    "林野": "林野_五视图.png", "苏晚": "苏晚_五视图.png", "赵铎": "赵铎_五视图.png",
    "陈铁柱": "陈铁柱_五视图.png", "苗苗": "苗苗_五视图.png", "周砚": "周砚_五视图.png",
    "韩麦": "韩麦_五视图.png", "沈青禾": "沈青禾_五视图.png", "季征": "季征_五视图.png",
    "林晚": "林晚_五视图.png",
}

def frame24(seconds):
    f = int(round(seconds * 24 / 17)) * 17
    return max(f, 124)

def concat_audio(files, out):
    if len(files) == 1:
        import shutil
        shutil.copy(files[0], out)
        return
    listf = out + ".list"
    with open(listf, "w", encoding="utf-8") as f:
        for p in files:
            f.write("file '%s'\n" % p)
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listf,
                    "-c", "copy", out], check=True)
    os.remove(listf)

def main(ep):
    script = open(os.path.join(ROOT, "剧集", ep, "剧本.md"), encoding="utf-8").read()
    vo = json.load(open(os.path.join(ROOT, "剧集", ep, "制作成果", "audio", "voice_list.json"), encoding="utf-8"))
    vo_by_scene = {}
    for v in vo:
        vo_by_scene.setdefault(v["scene"], []).append(v)

    parts = re.split(r"^## (EP\d+-SC\d+) (.+)$", script, flags=re.M)
    shots = []
    vdir = os.path.join(ROOT, "剧集", ep, "制作成果", "videos")
    adir = os.path.join(ROOT, "剧集", ep, "制作成果", "audio")
    sdir = os.path.join(ROOT, "剧集", ep, "制作成果", "images", "场景")

    i = 1
    while i < len(parts) - 1:
        sc_id, sc_name, body = parts[i], parts[i+1], (parts[i+2] or "")
        i += 3
        m = re.match(r"EP\d+-SC(\d+)", sc_id)
        sc_num = int(m.group(1))
        scene_img = None
        if os.path.isdir(sdir):
            for f in sorted(os.listdir(sdir)):
                if f.startswith("%s-%02d_" % (ep, sc_num)):
                    scene_img = os.path.join(sdir, f)
                    break
        lines = vo_by_scene.get(sc_id, [])

        if not lines:
            who = guess_who(body, "林野")
            shots.append(mkshot(ep, len(shots)+1, sc_id, sc_name, who,
                                "%s。镜头缓慢推进，%s在画面中，神情紧绷。真人实拍剧照风格，电影级光影，写实肌肤材质，低饱和度灰蓝调加暖光高光，环境音持续。" % (sc_name, who),
                                None, 9, vdir))
            continue

        # 一场一个长镜：拼接全部台词音频
        files = [os.path.join(adir, v["file"]) for v in lines]
        merged = os.path.join(adir, "merged_%s.wav" % sc_id)
        concat_audio(files, merged)
        dur = sum(v["dur"] for v in lines) + 2.5
        who = lines[0]["who"]
        txts = "；".join(v["text"][:12] for v in lines[:2])
        shots.append(mkshot(ep, len(shots)+1, sc_id, sc_name, who,
                            "%s。%s（%s）：「%s」真人实拍剧照风格，电影级光影，写实肌肤材质，低饱和度灰蓝调加暖光高光，人物在画面中心，口型与台词同步，对白与镜头同长。" % (
                                sc_name, who, "旁白" if lines[0]["vo"] else "台词", txts),
                            merged, dur, vdir))

    out = os.path.join(ROOT, ".scripts", "shots_%s.json" % ep)
    json.dump(shots, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(ep, "shots:", len(shots), "| total %.1fs" % sum(s["seconds"] for s in shots))
    for s in shots:
        print("  %s %4.0fs %-12s %-6s audio=%s" % (s["id"], s["seconds"], s["scene"], s["who"], bool(s["ref_audio"])))

def mkshot(ep, n, sc_id, sc_name, who, prompt, audio, dur, vdir):
    sheet = os.path.join(ROOT, "设定集", "人物板", CHAR_SHEET.get(who, CHAR_SHEET["林野"]))
    scene_img = None
    sdir = os.path.join(ROOT, "剧集", ep, "制作成果", "images", "场景")
    m = re.match(r"EP\d+-SC(\d+)", sc_id)
    if os.path.isdir(sdir):
        for f in sorted(os.listdir(sdir)):
            if f.startswith("%s-%02d_" % (ep, int(m.group(1)))):
                scene_img = os.path.join(sdir, f)
                break
    refs = [sheet] + ([scene_img] if scene_img else [])
    return {
        "id": "%s-S%02d" % (ep, n), "ep": ep, "scene": sc_id, "name": sc_name,
        "who": who, "prompt": prompt,
        "ref_images": refs, "ref_audio": audio,
        "seconds": round(dur, 1), "frames": frame24(dur),
        "out": os.path.join(vdir, "%s-S%02d_%s.mp4" % (ep, n, sc_name[:10])),
    }

def guess_who(body, default):
    for c in CHAR_SHEET:
        if c in body[:60]:
            return c
    return default

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "EP01")

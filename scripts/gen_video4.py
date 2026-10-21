# -*- coding: utf-8 -*-
"""v4 视频生成器：人物五视图 + 场景板双参考，生成带人镜头，可传入台词音频
用法: python gen_video4.py EP01 [shot_id]
"""
import json, os, sys, time, hashlib, urllib.request, urllib.parse, uuid

BASE = "http://127.0.0.1:8188"
WF_PATH = os.environ.get("COMFY_WF", r"D:\comfyUI\workflows\minimax_h3_r2v_native.json")  # 工作流路径可用环境变量覆盖
ROOT = os.environ.get("DRAMA_ROOT", r"D:\个人资料\网文创作\末日求生_短剧")  # 项目根可用环境变量覆盖

def post_json(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))

def get_json(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def upload(local, subfolder):
    fn = os.path.basename(local)
    boundary = uuid.uuid4().hex
    with open(local, "rb") as f:
        buf = f.read()
    parts = []
    for name, val in [("type", "input"), ("subfolder", subfolder)]:
        parts.append(("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n" % (boundary, name, val)).encode("utf-8"))
    parts.append(("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\nContent-Type: image/png\r\n\r\n" % (boundary, fn)).encode("utf-8"))
    parts.append(buf)
    parts.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    req = urllib.request.Request(BASE + "/upload/image", data=b"".join(parts),
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))

def download(url, out_path):
    with urllib.request.urlopen(BASE + url, timeout=300) as r:
        buf = r.read()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(buf)
    return len(buf)

def seed_for(i):
    return int(hashlib.sha1(i.encode("utf-8")).hexdigest()[:8], 16) % 999999 + 1

def img_ref(up):
    n = up["name"]; s = up.get("subfolder", "")
    return (s + "/" + n) if s else n

def aud_ref(up):
    n = up["name"]; s = up.get("subfolder", "")
    return (s + "/" + n) if s else n

def run_task(wf, t):
    wf = json.loads(json.dumps(wf))
    # 参考图：人物五视图 + 场景板
    load_ids = []
    for local in t["ref_images"]:
        up = upload(local, "drama_%s" % t["ep"])
        lid = str(int(max(int(k) for k in wf if k.isdigit())) + 1 + len(load_ids))
        wf[lid] = {"inputs": {"image": img_ref(up)}, "class_type": "LoadImage", "_meta": {"title": "LoadImage"}}
        load_ids.append(lid)
    wf["2"]["inputs"]["ref_images"] = [[lid, 0] for lid in load_ids]
    # 参考音频（台词）
    if t.get("ref_audio"):
        aup = upload(t["ref_audio"], "drama_%s" % t["ep"])
        # LoadAudio 节点
        aid = str(int(max(int(k) for k in wf if k.isdigit())) + 1 + len(load_ids) + 1)
        wf[aid] = {"inputs": {"audio": aud_ref(aup)}, "class_type": "LoadAudio", "_meta": {"title": "LoadAudio"}}
        wf["2"]["inputs"]["ref_audios"] = [[aid, 0]]
    wf["2"]["inputs"]["prompt"] = t["prompt"]
    wf["2"]["inputs"]["width"] = 1088
    wf["2"]["inputs"]["height"] = 1920
    wf["2"]["inputs"]["length"] = t["frames"]
    wf["2"]["inputs"]["ref_image_size"] = "match"
    wf["15"]["inputs"]["noise_seed"] = t.get("seed") or seed_for(t["id"])
    wf["12"]["inputs"]["filename_prefix"] = "drama_video/%s" % t["id"]
    resp = post_json("/prompt", {"prompt": wf, "client_id": "gen-video4"})
    if resp.get("error"):
        raise RuntimeError("validate: " + json.dumps(resp["error"], ensure_ascii=False)[:500])
    pid = resp["prompt_id"]
    waited = 0
    while waited < 5400:
        h = get_json("/history/" + pid, timeout=30)
        if h and pid in h:
            entry = h[pid]
            if entry.get("status", {}).get("status_str") == "error":
                raise RuntimeError("exec: " + json.dumps(entry.get("status"), ensure_ascii=False)[:400])
            outs = entry.get("outputs", {})
            for node_out in outs.values():
                vids = []
                for key in ("videos", "gifs", "images"):
                    for f in node_out.get(key) or []:
                        if str(f.get("filename", "")).lower().endswith((".mp4", ".webm", ".mov")):
                            vids.append(f)
                for v in vids:
                    q = "filename=%s&subfolder=%s&type=%s" % (
                        urllib.parse.quote(v["filename"]),
                        urllib.parse.quote(v.get("subfolder", "")),
                        urllib.parse.quote(v.get("type", "output")))
                    size = download("/view?" + q, t["out"])
                    return {"ok": True, "file": v["filename"], "bytes": size, "seconds": waited}
        time.sleep(5)
        waited += 5
    raise RuntimeError("timeout: " + t["id"])

def main():
    ep = sys.argv[1]
    only = sys.argv[2] if len(sys.argv) > 2 else None
    shots = json.load(open(os.path.join(ROOT, ".scripts", "shots_%s.json" % ep), encoding="utf-8"))
    wf = json.load(open(WF_PATH, encoding="utf-8"))
    print("共 %d 镜" % len(shots), flush=True)
    for i, t in enumerate(shots, 1):
        if only and t["id"] != only:
            continue
        if os.path.exists(t["out"]):
            print("[%d/%d] %s 已存在，跳过" % (i, len(shots), t["id"]), flush=True)
            continue
        t0 = time.time()
        try:
            res = run_task(wf, t)
            print("[%d/%d] %s OK %.0fs" % (i, len(shots), t["id"], time.time() - t0), flush=True)
        except Exception as e:
            print("[%d/%d] %s FAIL %s" % (i, len(shots), t["id"], e), flush=True)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""80 集批量构建驱动：parse_vo -> gen_tts -> plan_shots4 -> gen_video4 -> assemble6。
- ComfyUI 健康监控、挂了自动用 .venv 的 python 拉起
- 断点续跑（batch_state.json）、失败集隔离、末尾统一重试一次
用法: python run_all.py [--start 2] [--end 80]
"""
import json, os, subprocess, sys, time, urllib.request

ROOT = os.environ.get("DRAMA_ROOT", r"D:\个人资料\网文创作\末日求生_短剧")
S = os.path.join(ROOT, ".scripts")
COMFY_DIR = r"D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI (1)\ComfyUI"
COMFY_PY = os.path.join(COMFY_DIR, ".venv", "Scripts", "python.exe")
STATE = os.path.join(S, "batch_state.json")
LOG = os.path.join(S, "batch.log")
DONE_FLAG = os.path.join(S, "BATCH_DONE")


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (time.strftime("%m-%d %H:%M:%S"), msg))


def comfy_up():
    try:
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
        return True
    except Exception:
        return False


def start_comfy():
    log("ComfyUI down -> restarting")
    subprocess.Popen(
        [COMFY_PY, "main.py"], cwd=COMFY_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        stdout=open(os.path.join(S, "comfyui.log"), "a"),
        stderr=open(os.path.join(S, "comfyui.err"), "a"),
    )
    for _ in range(48):  # 最多等 4 分钟
        if comfy_up():
            log("ComfyUI up again")
            return True
        time.sleep(5)
    log("ComfyUI restart FAILED")
    return False


def sh(pyfile, ep):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, os.path.join(S, pyfile), ep],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    tail = ((r.stdout or "") + (r.stderr or ""))[-300:].replace("\n", " ")
    log("%s %s rc=%d %s" % (ep, pyfile, r.returncode, tail))
    return r.returncode == 0


def missing_shots(ep):
    p = os.path.join(S, "shots_%s.json" % ep)
    if not os.path.exists(p):
        return None
    shots = json.load(open(p, encoding="utf-8"))
    return [s["id"] for s in shots if not os.path.exists(s["out"])]


def build(ep, state):
    log("=== %s START ===" % ep)
    ok = sh("parse_vo.py", ep)
    if ok:
        ok = sh("gen_tts.py", ep)
    if ok:
        ok = sh("plan_shots4.py", ep)
    if ok:
        for attempt in range(3):
            miss = missing_shots(ep)
            if not miss:
                break
            log("%s render attempt %d: missing %d shots [%s]" % (ep, attempt + 1, len(miss), ",".join(miss)))
            if not comfy_up() and not start_comfy():
                ok = False
                break
            sh("gen_video4.py", ep)
        miss = missing_shots(ep)
        if miss:
            log("%s RENDER INCOMPLETE after retries [%s]" % (ep, ",".join(miss)))
            ok = False
    if ok:
        ok = sh("assemble6.py", ep)
    state[ep] = "done" if ok else "failed"
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("=== %s %s ===" % (ep, state[ep].upper()))
    return ok


def main():
    a = {"start": 2, "end": 80}
    it = iter(sys.argv[1:])
    for x in it:
        if x == "--start":
            a["start"] = int(next(it))
        elif x == "--end":
            a["end"] = int(next(it))
    eps = ["EP%02d" % i for i in range(a["start"], a["end"] + 1)]
    state = {}
    if os.path.exists(STATE):
        state = json.load(open(STATE, encoding="utf-8"))
    if not comfy_up():
        start_comfy()
    log("BATCH RUN eps %s..%s (done=%d failed=%d)" % (
        eps[0], eps[-1],
        sum(1 for v in state.values() if v == "done"),
        sum(1 for v in state.values() if v == "failed")))
    for ep in eps:
        if state.get(ep) == "done":
            continue
        build(ep, state)
    for ep in [e for e in eps if state.get(e) == "failed"]:
        log("RETRY FAILED %s" % ep)
        build(ep, state)
    done = [e for e in eps if state.get(e) == "done"]
    bad = [e for e in eps if state.get(e) != "done"]
    log("BATCH COMPLETE: %d/%d done%s" % (len(done), len(eps), (" failed=%s" % bad) if bad else ""))
    if not bad:
        open(DONE_FLAG, "w", encoding="utf-8").write(
            "all %d episodes done at %s\n" % (len(eps), time.strftime("%Y-%m-%d %H:%M:%S")))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""ComfyUI 看护工具：status / start / restart。
用法: python comfy_ctl.py status|start|restart
"""
import os, subprocess, sys, time, urllib.request

COMFY_DIR = r"D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI (1)\ComfyUI"
COMFY_PY = os.path.join(COMFY_DIR, ".venv", "Scripts", "python.exe")
S = os.path.join(os.environ.get("DRAMA_ROOT", r"D:\个人资料\网文创作\末日求生_短剧"), ".scripts")


def up():
    try:
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
        return True
    except Exception:
        return False


def pids():
    r = subprocess.run(["wmic", "process", "where",
                        "CommandLine like '%main.py%' and Name='python.exe'",
                        "get", "ProcessId"], capture_output=True, text=True)
    return [int(x) for x in r.stdout.split() if x.isdigit()]


def start():
    subprocess.Popen(
        [COMFY_PY, "main.py"], cwd=COMFY_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        stdout=open(os.path.join(S, "comfyui.log"), "a"),
        stderr=open(os.path.join(S, "comfyui.err"), "a"))
    for _ in range(48):
        if up():
            print("UP")
            return True
        time.sleep(5)
    print("START FAILED")
    return False


def restart():
    for pid in pids():
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    time.sleep(3)
    return start()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        print("UP" if up() else "DOWN")
    elif cmd == "start":
        print("OK" if (up() or start()) else "FAIL")
    elif cmd == "restart":
        print("OK" if restart() else "FAIL")

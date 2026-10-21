# -*- coding: utf-8 -*-
"""从剧本.md提取台词，生成配音单 voice_list.json 与字幕条目 subs.json。
台词格式：角色（括号说明）：台词内容   或  [VO] 角色：台词
"""
import json, os, re, sys

ROOT = os.environ.get("DRAMA_ROOT", r"D:\个人资料\网文创作\末日求生_短剧")  # 项目根可用环境变量覆盖

VOICES = {
    "林野": ("zh-CN-YunxiNeural", "+0%", "-2Hz"),
    "苏晚": ("zh-CN-XiaoxiaoNeural", "+0%", "+0Hz"),
    "店员": ("zh-CN-YunjianNeural", "+0%", "-3Hz"),
    "理货员": ("zh-CN-YunjianNeural", "+0%", "-3Hz"),
    "路人甲": ("zh-CN-YunyangNeural", "+0%", "+0Hz"),
}

def parse(ep):
    txt = open(os.path.join(ROOT, "剧集", ep, "剧本.md"), encoding="utf-8").read()
    items = []
    cur_scene = None
    for line in txt.splitlines():
        m = re.match(r"## (EP\d+-SC\d+) ", line)
        if m:
            cur_scene = m.group(1)
            continue
        m = re.match(r"\[VO\]\s*([^:：]{1,12})[:：]\s*(.+)", line)
        if m:
            items.append({"scene": cur_scene, "who": m.group(1), "text": m.group(2).strip(), "vo": True})
            continue
        m = re.match(r"(\S+?)（[^）]*）[:：]\s*(.+)", line)
        if m:
            who = m.group(1)
            if who in ("△", "[转场]", "[画面文字]"):
                continue
            items.append({"scene": cur_scene, "who": who, "text": m.group(2).strip(), "vo": False})
    return items

if __name__ == "__main__":
    ep = sys.argv[1] if len(sys.argv) > 1 else "EP01"
    items = parse(ep)
    out = os.path.join(ROOT, ".scripts", "vo_%s.json" % ep)
    json.dump(items, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for i, it in enumerate(items, 1):
        v = VOICES.get(it["who"], ("zh-CN-YunxiNeural", "+0%", "+0Hz"))
        print("%02d %s|%s|%s|%s" % (i, it["scene"], it["who"], v[0], it["text"][:24]))

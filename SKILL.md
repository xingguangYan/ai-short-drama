---
name: ai-short-drama
description: 从《剧本.md》批量生产竖屏短剧/漫剧成片（edge-tts 配音 → ComfyUI MiniMax H3 参考生视频 → 装配成片）。用于"做短剧/漫剧/竖屏剧集/批量生成剧集视频"类需求，配合本机 ComfyUI 与 RTX GPU。
---

# AI 竖屏短剧流水线

把每集一份 `剧本.md`（场标 `## EPxx-SC001 内 · 地点 · 时间`，台词 `角色（说明）：内容`，旁白 `[VO] 角色：内容`）做成一条 1088×1920、24fps、带人物语音的竖屏成片。成熟实例：《末日求生》80 集（`D:\个人资料\网文创作\末日求生_短剧`）。

## 何时触发

用户要做短剧/漫剧/竖屏剧集、要把小说改剧、要"批量出集"、"生成第 N 集视频"、"继续生成后续剧集"。不动纯文字写作（那是 story-* 技能的事），本技能的边界是**从已有剧本与资产到成片 mp4**。

## 五阶段（每集固定顺序）

1. **剧本解析** `scripts/parse_vo.py EPxx`：从 `剧本.md` 抽台词/旁白 → `.scripts/vo_EPxx.json`。
2. **TTS 配音** `scripts/gen_tts.py EPxx`：edge-tts 按角色声线合成 → `制作成果/audio/00N_角色.mp3` + `voice_list.json`。TTS 只有一个用途：**给 H3 当参考音源，驱动人物开口**；不进成片。
3. **分镜规划** `scripts/plan_shots4.py EPxx`：一场一个长镜，该场全部台词合并成 `merged_EPxx-SCxxx.wav` 当参考音频，人物五视图+场景板双参考图 → `shots_EPxx.json`。
4. **H3 渲染** `scripts/gen_video4.py EPxx`：本机 ComfyUI `minimax_h3_r2v_native.json`，逐镜生成含人物语音的视频（模型自带同步口型）。帧数必须 17 的倍数且 ≥124，24fps。
5. **装配** `scripts/assemble6.py EPxx`：九镜左右硬切拼接（无黑场），**只保留镜头自带的人物语音**，逐镜按 EBU 响度归一到对标片水平，输出 `成片/EPxx_成片.mp4`。

批量跑用 `scripts/run_all.py`（带 ComfyUI 健康监控、断点续跑、失败隔离）。ComfyUI 挂了用 `scripts/comfy_ctl.py` 重启。

## 铁律（违反必出事）

- **成片只留镜头自带人物语音**：H3 生成的音轨就是人物在说话（口型同步）。绝不叠加 TTS、不渲底部字幕、不留旁白叠加——每句话只能响一次。
- **H3 帧数 17 的倍数且 ≥124**；一镜 5-12 秒；参考图必须 `ref_images: [[id,0],...]` 列表式；上传接口不能多发 `image` 文本字段（500）。
- **ComfyUI 崩溃后必须用 `.venv` 的 python 重启**（standalone-env 的 python 无 torch）。工作流与 ComfyUI 路径见 `references/environment.md`。
- 剧本先行：没有 `剧本.md` 与该集场景板/人物五视图，不要进渲染。五视图=全身+正面+左侧面+右侧面+背面，保证人物不变形。

## 参考

- `references/pipeline.md`——五阶段逐个讲清、字段与目录约定、各脚本参数
- `references/environment.md`——ComfyUI/edge-tts/ffmpeg/PowerShell 全部踩坑与解法
- `references/spec.md`——对标片分析与成片验收规格（时长、响度、转场、人物在场）

## 部署

仓库与部署说明见 `references/deploy.md`（本地 git 仓库已建好，首次推送需要作者提供 GitHub 令牌）。项目级脚本主副本在项目的 `.scripts/`，技能内 `scripts/` 是可复制的通用版（`DRAMA_ROOT` 环境变量切项目）。

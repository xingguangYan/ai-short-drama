# ai-short-drama

# AI Short Drama
Skill for AI short drama batch production with MiniMax H3
> **从《剧本.md》到竖屏成片的一站式批量生产流水线。**
> 五阶段自动化 · MiniMax H3 原生音视频 · edge-tts 声线驱动 · ComfyUI 本地渲染

---

## 📛 技术栈徽章

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![ComfyUI](https://img.shields.io/badge/ComfyUI-0.30.0%2B-6B4FBB?style=flat-square)
![MiniMax H3](https://img.shields.io/badge/MiniMax_H3-R2V_Native-FF6B35?style=flat-square)
![edge-tts](https://img.shields.io/badge/edge--tts-Neural_Voices-0078D4?style=flat-square&logo=microsoftedge&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-EBU_R128-007808?style=flat-square&logo=ffmpeg&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)
![GPU](https://img.shields.io/badge/GPU-RTX_3060%2B-76B900?style=flat-square&logo=nvidia&logoColor=white)
![Output](https://img.shields.io/badge/Output-1088%C3%971920%20%7C%2024fps-black?style=flat-square)
![Status](https://img.shields.io/badge/Status-v1.0_Active-brightgreen?style=flat-square)

---

## 📖 这是什么

`ai-short-drama` 是一个面向 **AI 竖屏短剧/漫剧批量生产**的 Codex Skill。它的输入极其简单——每集一份符合格式约定的 `剧本.md`，以及该集的人物五视图和场景板；它的输出同样明确——一条 **1088×1920、24fps、带人物原生语音**的竖屏成片 MP4。

这个项目不试图做一个“万能视频生成器”。它的边界被写死在 SKILL.md 里：**从已有剧本与资产到成片 mp4**。纯文字写作不属于它，那是 `story-*` 技能的事。它解决的是产业链条上最枯燥、最重复、也最容易因为“第 47 集的第 3 场和第 12 集的光线不一致”而崩掉的那一段：**把已经定稿的东西，稳定地、批量地渲染出来。**

项目在 2026 年 10 月 22 日完成了 v1 的首次提交和多次迭代，包括部署文档修正和长镜头渲染超时从默认值放宽到 3 小时。从 commit 节奏看，这是一个从真实生产需求里长出来的工具，而不是一个先写框架再找用例的实验室项目。

---

## 🧭 它在你工作流里的位置

```
网文 / 小说 / 故事
       │
       ▼
  story-* 技能  ──→  剧本.md + 人物五视图 + 场景板
       │
       ▼
  ai-short-drama  ──→  成片/EPxx_成片.mp4
```

SKILL.md 明确写着：“不动纯文字写作（那是 story-* 技能的事），本技能的边界是从已有剧本与资产到成片 mp4”。这意味着你需要在进入这条流水线之前，已经把“这一集谁在什么地方说了什么话”想清楚，并且已经把人物的五视图（全身、正面、左侧面、右侧面、背面）和场景板准备好。**剧本先行**不是一句建议，而是铁律：没有 `剧本.md` 与该集场景板/人物五视图，不要进渲染。

---

## 🏗️ 五阶段流水线

每一集固定按顺序跑五个阶段。每个阶段都有独立的 Python 脚本，产物落盘，可以单独检查、单独重跑。

### 阶段一：剧本解析

**脚本**：`scripts/parse_vo.py EPxx`

从 `剧本.md` 中抽取台词和旁白，输出 `.scripts/vo_EPxx.json`。剧本的格式约定是场标 `## EPxx-SC001` 内包含“地点 · 时间”，台词写成 `角色（说明）：内容`，旁白写成 `[VO] 角色：内容`。这个阶段不调用任何模型，纯粹是结构化解析，速度快、结果稳定，跑完之后可以直接打开 JSON 核对台词有没有被漏掉或错拆。

### 阶段二：TTS 配音

**脚本**：`scripts/gen_tts.py EPxx`

用 `edge-tts` 按角色声线合成音频，产物是 `制作成果/audio/00N_角色.mp3` 和 `voice_list.json`。这里有一个容易误解的设计：**TTS 的唯一用途是给 H3 当参考音源**，驱动人物开口，它本身不进成片。成片里听到的人声是 H3 在生成视频时同步产出的原生音轨，不是这阶段合成的 TTS。

`edge-tts` 调用的是 Microsoft Edge 的在线神经网络语音服务，不需要 API Key，支持中文自然发音和多语言。项目对声线映射做过专门补丁，涉及“煤球/回声体五视图映射与女声/儿童声线”的同步修正。

### 阶段三：分镜规划

**脚本**：`scripts/plan_shots4.py EPxx`

一场戏一个长镜，该场全部台词合并成 `merged_EPxx-SCxxx.wav` 作为参考音频，配上人物五视图和场景板双参考图，输出 `shots_EPxx.json`。“一场一镜”的选择直接决定了后续渲染的粒度和时长约束：一镜 5–12 秒，不能更短，也不建议更长。

### 阶段四：H3 渲染

**脚本**：`scripts/gen_video4.py EPxx`

这是整条流水线里最重的一步。调用本机 ComfyUI 的 `minimax_h3_r2v_native.json` 工作流，逐镜生成**含人物语音**的视频。MiniMax H3 是开放权重的全模态视频模型，在同一次生成中同时输出画面与音轨，模型自带同步口型，因此成片里的说话声和嘴型是对齐的。

渲染有两个硬约束：**帧数必须是 17 的倍数且 ≥124**，帧率 24fps。参考图的传参方式必须是 `ref_images: [[id,0],...]` 的列表形式，上传接口不能多发 `image` 文本字段，否则会返回 500。`gen_video4.py` 的超时在近期被调整为 3 小时，专门为长镜头渲染的稳定性服务。

### 阶段五：装配成片

**脚本**：`scripts/assemble6.py EPxx`

九镜左右硬切拼接，**不留黑场**，只保留镜头自带的人物语音，逐镜按 EBU 响度归一到对标片水平，输出 `成片/EPxx_成片.mp4`。

“只保留镜头自带语音”是整条流水线最硬的一条铁律：H3 生成的音轨就是人物在说话，绝不叠加 TTS、不渲底部字幕、不留旁白叠加——**每句话只能响一次**。这条规则的目的是杜绝“口型在说 A，音轨在放 B”的双声叠音事故。

---

## ⚡ 批量跑：run_all 与 comfy_ctl

单集手动跑五个脚本是可行的，但批量出集的正确入口是：

```bash
python scripts/run_all.py
```

它带 **ComfyUI 健康监控、断点续跑和失败隔离**。某一集或某一镜挂掉，不会把整批任务拖死；下一次可以从断点继续，而不是从第 1 集重来。

ComfyUI 挂了或失联了，用：

```bash
python scripts/comfy_ctl.py
```

来重启。这里有一个极易踩的坑：**必须用 `.venv` 的 Python 来重启**，standalone-env 的 Python 没有装 torch，用它启动的 ComfyUI 会在模型加载阶段直接失败。

---

## 📋 剧本格式约定

流水线对剧本格式有严格的解析依赖。每一集的内容写在一个 `剧本.md` 里，场标格式为：

```
## EP01-SC001  内 · 咖啡馆 · 日
```

台词格式：

```
林薇（低声）：你到底有没有看过那份合同？
```

旁白格式：

```
[VO] 旁白：三天前，她还以为一切都在掌控之中。
```

场标行里的“内/外 · 地点 · 时间”是分镜规划阶段识别场景的依据，格式错一个字符，解析就可能漏掉整场戏。

---

## 🖼️ 资产要求：五视图与场景板

人物五视图 = **全身 + 正面 + 左侧面 + 右侧面 + 背面**。SKILL.md 把这一点放在铁律里，理由是“保证人物不变形”。H3 的参考生视频模式依赖多角度参考图来约束人物在镜头中的一致性，缺一个角度，模型就多一分自由发挥的空间，而这个空间通常以“脸变了”或“衣服颜色不对”的形式兑现。

场景板是每一场戏的空间基准。分镜规划阶段把人物五视图和场景板作为双参考图送进 H3，因此场景板的构图、光线和色调会直接影响最终画面的基调。

---

## 🔧 环境与部署

仓库的 `references/` 目录下有四份文档，各有明确分工：

| 文件 | 内容 |
|---|---|
| `deploy.md` | 部署步骤与状态说明 |
| `environment.md` | ComfyUI、工作流、模型路径的具体配置 |
| `pipeline.md` | 五阶段流水线的详细说明 |
| `spec.md` | 剧本格式与技术规格 |

部署的核心链路是：Python 环境（建议 `.venv`）→ `edge-tts` → ComfyUI 0.30.0 或更高版本 → MiniMax H3 的 R2V 工作流和模型权重 → FFmpeg（用于装配阶段的编码和响度归一）。ComfyUI 的路径和工作流文件位置在 `references/environment.md` 里写死，换机器时需要同步修改。

`scripts/` 目录下的七个脚本构成了完整的工具链：

| 脚本 | 职责 |
|---|---|
| `parse_vo.py` | 剧本解析 |
| `gen_tts.py` | edge-tts 配音 |
| `plan_shots4.py` | 分镜规划 |
| `gen_video4.py` | H3 渲染 |
| `assemble6.py` | 装配成片 |
| `run_all.py` | 批量调度 + 断点续跑 |
| `comfy_ctl.py` | ComfyUI 启停控制 |

`agents/openai.yaml` 是 Codex 侧的 agent 配置文件，定义了这个技能如何被 Codex 识别和调用。

---

## ⚠️ 铁律与故障排查

SKILL.md 把最容易导致翻车的约束集中放在“铁律”一节，每一条都对应一个真实踩过的坑：

**铁律一：成片只留镜头自带人物语音。** 绝不叠加 TTS，不渲底部字幕，不留旁白叠加。每句话只能响一次。违反这条的后果是双声叠音，口型和声音对不上。

**铁律二：H3 帧数必须是 17 的倍数且 ≥124。** 帧率 24fps，一镜 5–12 秒。帧数不对，生成会失败或输出时长异常。

**铁律三：参考图必须是 `ref_images: [[id,0],...]` 列表式。** 上传接口不能多发 `image` 文本字段，否则 500。

**铁律四：ComfyUI 崩溃后必须用 `.venv` 的 Python 重启。** standalone-env 的 Python 没有 torch，用它重启等于换了一个没有引擎的车壳。

**铁律五：剧本先行。** 没有 `剧本.md`、场景板和人物五视图，不要进渲染。

---

## 🧩 它适合谁，不适合谁

**适合**：已经在做竖屏短剧/漫剧、有相对稳定的剧本产出流程、手上有 RTX GPU 和 ComfyUI 环境、需要把“第 N 集到第 N+10 集”一次性跑出来的人。80 集《末日求生》是 SKILL.md 里提到的成熟实例，说明这条流水线被真实的长篇系列验证过。

**不适合**：想从一句点子直接生成短剧的人（需要先有剧本和资产）；没有本地 GPU、不想维护 ComfyUI 环境的人；需要多模型自由切换、而不是锁定 MiniMax H3 的人。

---

## 📌 版本状态

项目于 **2026 年 10 月 22 日** 发布 v1，同日完成部署文档修正、声线映射补丁和长镜头渲染超时调整。`scripts/gen_video4.py` 的超时已放宽到 3 小时，`deploy.md` 的状态表述经过修正。这是一个仍在活跃迭代的早期工具，README 本身只有一行占位文本，真正的规格细节分散在 `SKILL.md` 和 `references/` 的四份文档里。

---

## 🔗 相关链接

- **仓库**：[github.com/xingguangYan/ai-short-drama](https://github.com/xingguangYan/ai-short-drama)
- **MiniMax H3 模型**：[huggingface.co/MiniMaxAI/MiniMax-H3](https://huggingface.co/MiniMaxAI/MiniMax-H3)
- **edge-tts**：[github.com/rany2/edge-tts](https://github.com/rany2/edge-tts)

---

*本文档基于仓库 SKILL.md、scripts/ 与 references/ 目录的实际内容，以及 MiniMax H3 和 edge-tts 的公开技术资料整理撰写。*

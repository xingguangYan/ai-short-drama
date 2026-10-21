# 流水线详述

## 项目目录约定

```
<项目根>/
├── 剧集/EPxx/
│   ├── 剧本.md            # 输入：场标 + 台词 + [VO] + [画面文字]
│   ├── 分镜.md  视觉设定.md  图片提示词.md  视频提示词.md
│   └── 制作成果/
│       ├── audio/         # 00N_角色.mp3、merged_EPxx-SCxxx.wav、voice_list.json
│       ├── images/场景/    # EPxx-NN_场景名.png（场景板，逐场一张）
│       ├── videos/        # EPxx-SNN_场名.mp4（H3 成品镜头）
│       └── 成片/          # EPxx_成片.mp4
├── 设定集/人物板/           # 角色_五视图.png
├── .scripts/              # 流水线脚本与 shots_EPxx.json、vo_EPxx.json、batch_state.json、batch.log
└── 40359102044-1-16.mp4   # 对标参考片（保留，勿删）
```

环境变量 `DRAMA_ROOT` 指向项目根；不设则用脚本内置默认（末日求生项目）。

## 阶段 1：剧本解析（parse_vo.py）

- 剧本格式：`## EPxx-SCNNN 内/外 · 地点 · 时间`；台词 `角色（动作/神态）：内容`；旁白 `[VO] 角色：内容`；`[画面文字]`、`△`、`[音效]`、`[转场]` 不抽。
- 产物 `.scripts/vo_EPxx.json`：`{scene, who, text, vo}`，`vo=true` 为旁白。
- 旁白处理：旁白照样合成 TTS、照常进 merged 参考音频——H3 会把第一人称旁白渲染成**角色本人在镜头里说**，成片里自然出现一次。不要在装配阶段再叠旁白。

## 阶段 2：TTS（gen_tts.py）

- edge-tts。声线表在脚本内 `VOICES`，按角色名映射（男声 Yunxi/Yunjian/Yunyang，女声 Xiaoxiao）。
- 语速：台词 +8%、旁白 +15%（`--rate` 只能传一次，合并计算）。
- edge-tts 必须 ≥7.3.1（7.2.8 的 GEC token 会 403）。
- 脚本幂等：mp3 已存在则跳过并回读时长。
- 产物 `voice_list.json`（含每条 dur，供分镜对位用）。

## 阶段 3：分镜规划（plan_shots4.py）

- 一场 = 一个长镜头：该场全部台词 mp4?（mp3）顺序 concat 成 `merged_EPxx-SCxxx.wav` 做 H3 参考音频；镜长 = 台词总时长 + 2.5s。
- 帧数换算：`int(round(秒*24/17))*17`，下限 124。
- 该场无台词：走环境交代镜（`ref_audio=None`，9 秒，人物在场，镜头缓慢推进）。
- 参考图：`[人物五视图, 该场场景板]`；人物取该场首个说话人，未命中则从场记 body 猜角色名。
- 产物 `shots_EPxx.json`：每镜 `{id, scene, who, prompt, ref_images, ref_audio, seconds, frames, out}`，`out` 决定渲染跳过/续跑。
- prompt 模板：`「场名。角色（台词/旁白）：『台词前两句』真人实拍剧照风格，电影级光影，写实肌肤材质，低饱和度灰蓝调加暖光高光，人物在画面中心，口型与台词同步，对白与镜头同长。」`

## 阶段 4：H3 渲染（gen_video4.py）

- 本机 ComfyUI `http://127.0.0.1:8188`，工作流 `D:\comfyUI\workflows\minimax_h3_r2v_native.json`，节点 2 `MiniMaxH3ReferenceToVideo`。
- 每镜：上传五视图+场景板（`/upload/image`，subfolder=`drama_EPxx`）→ 动态插 LoadImage 节点 → `ref_images=[[lid,0],...]` → 上传 merged 参考音频，插 LoadAudio，`ref_audios=[[aid,0]]` → 设 prompt/宽高/帧数 → 提交轮询 `/history/<pid>` → 下载视频。
- 出图尺寸固定 1088×1920，`ref_image_size="match"`，seed 由 shot id 的 sha1 派生（可复现）。
- 单镜渲染 6-40 分钟；脚本幂等（`out` 存在即跳过）。
- **H3 输出的音轨就是人物语音**：模型按参考音频生成同步口型与语音。转写抽查（faster-whisper small 离线）可核验每镜说了哪几句；模型可能漏句、缩词（如"防潮布"→"房"），漏关键句才考虑重渲染（改 seed）。

## 阶段 5：装配（assemble6.py）

- 逐镜 ffmpeg：`scale=1088:1920,fps=24` + 按 EBU 实测响度给 `volume=±dB`（增益限 ±8dB）+ `alimiter=0.97` + 统一 mono 44100 → concat 硬切 → 成片。
- 不加 TTS、不加字幕、不加黑场转场、不加转场特效——对标片就是硬切。
- 成片验收标准见 `spec.md`。

## 批量（run_all.py）

- 顺序跑 EP02..EP80：parse_vo → gen_tts → plan_shots4 → gen_video4（带 3 次重试 + ComfyUI 健康检查，挂了自动重启）→ assemble6。
- 状态 `.scripts/batch_state.json`（每集 done/failed），断了重跑自动续。
- 日志 `.scripts/batch.log`。失败集隔离，不阻塞后续集。
- 用心跳（Codex automation）周期性检查：驱动挂了拉起来、全跑完通知作者。

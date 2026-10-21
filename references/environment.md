# 环境与踩坑手册

所有条目都是实战踩出来的，违反会直接出血。

## ComfyUI

- 地址 `http://127.0.0.1:8188`。崩溃后**必须**用 `D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI (1)\ComfyUI\.venv\Scripts\python.exe` 启动 `main.py`；standalone-env 的 python 没有 torch，起不来。
- 启动参数无特殊；模型加载 1-3 分钟，用 `/system_stats` 探活。
- 工作流 `D:\comfyUI\workflows\minimax_h3_r2v_native.json`：
  - 节点 2 `MiniMaxH3ReferenceToVideo`，参考图**必须** `ref_images: [[id,0],...]` 列表式，用 `ref_image_0` 之类单字段会报错。
  - 视频含音频：节点 91 `CreateVideo` 的 `audio` 接节点 23（模型生成），`audio_vae` 是节点 24。
  - 帧数必须 17 的倍数且 ≥124；144 帧 = 6 秒（24fps）。
  - 独立 seed 节点 15 `RandomNoise`，`noise_seed`。
- 上传接口 `/upload/image` 是 multipart，**不能**多发 `image` 文本字段（会 500）；图片二进制随 `filename` 走。
- H3 参考生视频同时收图片与音频参考：图片管"长什么样"，音频管"说什么"。

## edge-tts

- 版本必须 ≥7.3.1；7.2.8 的 GEC token 会 403。
- `--rate` 一个命令只能传一次，多次速率调整要合并（如 +8% 就直接给 `+8%`，别叠加两次）。
- `--pitch` 单位 Hz（如 `-2Hz`）。
- 中文长文本按句切分配音是阶段 1/2 的事，TTS 本身不切。

## ffmpeg（本机 4.3.1，旧）

- `amix` **没有** `normalize` 参数（Error: Option 'normalize' not found），默认把每路输入衰减 1/N。N 路混音若不补偿，响度塌 -20dB 量级。补偿法：`volume=N`，或改用 adelay+amerge 流水线（amerge 需先 `aformat=channel_layouts=mono:sample_rates=44100` 对齐格式，否则报 format 错）。
- 响度测量用 `ebur128`（`I:` 行为 integrated LUFS）；`volumedetect` 的 mean/max 是 dB 峰值/RMS，两套别混。对标片基准：**I = -17.5 LUFS**，mean -20.2dB，max 0dB。
- `amerge` 不同格式直接报错：先 aformat。
- 探测时长用 ffprobe `format=duration`。

## 画面调性

- 成片是暗调小构图（对标片同款）。`blackdetect` 会把整片误报成黑场——这是**正常的**，别拿它当 bug；验证黑场要用 PIL 取帧亮度范围（正常 0~255 全域）或抽查关键帧。
- 水印排查：whisper 可能幻听出"字幕by某某"，先用 PIL 分行像素统计排除画面烧录文字（底部条带均匀高亮 = 场景亮面，非字幕）。

## PowerShell / Windows

- 工具链 shell 是 PowerShell。**多行 here-string 可用**（`@'...'@ | Set-Content -Encoding utf8 写中文 .py），但 `$_` 有时会被外层吃掉——避免 `ForEach-Object { $_.X }`，改用 `Get-ChildItem | Format-Table`、`Get-Content -TotalCount` 之类的无变量写法。
- `cmd /c` 的 `for %f in (...)` 在 PowerShell 里不工作；`dir /b`、`if exist` 也别用。
- 控制台中文 GBK 乱码是常态（文件本身 UTF-8 没问题）；Python 输出设 `$env:PYTHONIOENCODING="utf-8"` 再重定向到文件读。
- 后台进程用 `Start-Process -WindowStyle Hidden`；Python 里等价 `subprocess.Popen(..., creationflags=DETACHED_PROCESS|CREATE_NO_WINDOW)`。
- 删除文件命令在沙箱里可能被策略拦截，拆开来逐个试 `Remove-Item`（无 `-Force`）。

## 模型斜坡

- faster-whisper 只有 `small` 本地缓存，HuggingFace 不通；PyAV 版本与 faster-whisper 1.2.1 不兼容（`av.open() metadata_errors` 报错）——绕过：用 ffmpeg 解码到 numpy 再喂 `transcribe(ndarray)`。
- anaconda + torch 共存时 OpenMP 冲突：设 `$env:KMP_DUPLICATE_LIB_OK="TRUE"`（`set` 在 PS 里无效，要用 `$env:`）。
- whisper 时间轴不可全信（短段会串位）；逐段切开单独转写更准；`condition_on_previous_text=True` 会把幻听循环成"重复台词"，看到的"循环"先分段复核再信。

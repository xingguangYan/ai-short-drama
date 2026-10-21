# 部署说明

## 本地仓库

技能目录本身已是 git 仓库（`git init` 于此目录）：

```
ai-short-drama/
├── SKILL.md
├── references/   pipeline.md · environment.md · spec.md · deploy.md
└── scripts/      parse_vo · gen_tts · plan_shots4 · gen_video4 · assemble6 · run_all · comfy_ctl
```

- 提交：`git add -A && git commit -m "..."`
- .gitignore 已排除 `__pycache__/`、日志。

## 推送到 GitHub

需要作者提供一次鉴权（二选一）：

1. 在 GitHub 建一个空仓库（如 `ai-short-drama`，建议私有），生成 classic PAT（勾 `repo`），把令牌存到本地文件 `D:\个人资料\网文创作\末日求生_短剧\.github_token`（一行纯令牌，别贴在聊天里）。
2. 或者在本机装 GitHub CLI 并执行一次 `gh auth login`（交互登录）。

随后执行：

```powershell
cd C:\Users\Administrator\.codex\skills\ai-short-drama
$tok = (Get-Content "D:\个人资料\网文创作\末日求生_短剧\.github_token").Trim()
git remote add origin "https://$tok@github.com/<你的用户名>/ai-short-drama.git"
git push -u origin main
# 推完删掉 origin 里的令牌引用，改回不含令牌的地址，避免令牌留在 .git/config
git remote set-url origin "https://github.com/<你的用户名>/ai-short-drama.git"
```

推完后把本文件里的"首次推送需要作者提供 GitHub 令牌"一句更新为实际仓库地址。

## 项目内容（可选）

如需把《末日求生》项目本身（剧本、成片）也纳入版本管理：在项目根另建仓库；`剧集/*/制作成果/videos` 与 `成片` 体积大，进 .gitignore（或用 Git LFS）。默认只推技能本体。

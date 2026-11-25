# V5 GitHub Pages 云端部署版

1. 在 https://github.com/new 创建 Public 空仓库（建议 gta6-pc-radar，不勾选 README 等初始化选项）。
2. 解压 ZIP，进入解压后含 .github、site、scripts 的目录。使用 GitHub Desktop 添加本地仓库并发布，或者在 Git Bash/终端运行以下命令（把 USERNAME 换成账号名）。不要上传 ZIP 本身；务必包含隐藏的 .github 和 .gitignore。

```sh
git init -b main
git add .
git commit -m "Deploy GTA VI Radar V5"
git remote add origin https://github.com/USERNAME/gta6-pc-radar.git
git push -u origin main
```

3. 仓库 Settings → Pages → Build and deployment → Source → GitHub Actions。
4. 确认 Actions 已启用且允许工作流写入仓库内容（Settings → Actions → General；组织政策可能限制）。Actions → Update radar and publish → Run workflow → main。首次 push 可能发生在 Pages 配置之前，设置完成后重新运行即可。
5. 等工作流成功，Settings → Pages 查看实际访问网址。通常为 `https://USERNAME.github.io/gta6-pc-radar/`。

无需自行申请 AI API 或 GitHub token：工作流使用内置 GITHUB_TOKEN。每5分钟是计划调度，可能延迟或跳过；页面每20秒请求已发布数据。公共仓库通常可用免费标准 runner；长期无活动时 GitHub 可能停用定时任务。GitHub API 检查轮转每次最多15个仓库，避免频繁请求。

首次页面可能为历史快照，实际采集结果以来源状态为准。站点公开，不得将密钥提交进仓库。工作流会提交 site/data/state.json 保存历史；长期运行历史会增长。完整评分、证据黑匣子及限制见 FEATURES.md。

官方说明：https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

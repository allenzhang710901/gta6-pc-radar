GTA VI 进度雷达 5.2 验收补丁（替代 5.1，不是完整安装包）
1. GitHub Desktop 选中 gta6-pc-radar，Fetch origin / Pull origin，获取最新历史。
2. Repository -> Show in Explorer。解压补丁，将 .github、scripts、site、tests 四个目录合并复制到仓库根目录，同名文件选择替换。不要删除任何原文件。
3. 补丁不包含 site/data/state.json；保留数据库和 .git。确认 GitHub Desktop 的变更不含删除/覆盖数据库。
4. Commit to main（Radar 5.2 reliability audit），Push origin。若远端有新提交，先 Pull 再 Push；不要强推。
5. 到 Actions 查看此次新推送触发的任务，update 和 deploy 都应为绿色。不要重复启动旧任务。网站 Ctrl+F5，检查左上 5.2 验收版、最近扫描、数据源、排行榜和预测。
6. GitHub 正常后再上传 EdgeOne 5.2 联网 ZIP。两个版本读取同一份数据。

验收：27项后端测试通过；两个网页在 Chromium 中以模拟 fetch、localStorage 测试读取、语言切换、筛选、详情保留、过期预测、坏数据、拒绝旧快照、手机宽度；EdgeOne 模拟主接口故障后备用接口成功。未实际验证真实跨域请求及定时调度。
评分仍为第三方证据的规则分析，不是开发真实完成率；无新证据不强行提高评分。预计时间仍为上游预测及单独假设模型，不是独立统计预测。项目候选仍待核查。每5分钟为计划调度，GitHub可能跳过，未接入外部调度器。数据库达到30MB时工作流警告；长期增长需要分卷归档。没有承诺零故障。

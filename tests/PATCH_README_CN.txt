GTA VI 进度雷达 V6.0 多维评分更新补丁（适用 V5 / V5.1 / V5.2）

1. GitHub Desktop 先 Fetch origin，如出现 Pull origin 就同步。
2. Repository → Show in Explorer，打开现有 gta6-pc-radar 仓库。
3. 将本包解压后的文件、目录合并复制到仓库根目录，替换同名文件。
   不删除 .git，不覆盖 site/data/state.json（本补丁不含数据库）。
4. GitHub Desktop 提交说明 Radar V6 multidimensional scoring，然后 Push origin。
5. Actions → Update radar and publish，检查最新任务 update / deploy 均成功。
   如需手动运行，用 Run workflow（main），不要反复 Re-run 旧任务。
6. 打开原网站 Ctrl+F5。GitHub 成功后，再上传 V6 EdgeOne ZIP。

新评分：阶段20、性能20、画面20、剧情15、稳定性15、操控10。
单来源证据包计算，未知维度不给分但不视作失败；覆盖权重单独展示。
PortWatch 标记自身观察为 B（75%折算），其他第三方报告 C（60%），
非明确平均 FPS 的严格分折算不超过55%。这不是统计概率或独立测试。
外部排名：PortWatch 按其公开评分公式重算；PC Race 为页面展示顺序。
显卡筛选来自 PortWatch 的显卡标签，未记录显示未知。
旧版评分及历史黑匣子保持不变，新扫描会记录评分版本变化。
预测仍是外部估计和假设情景，不是经验证的发布日期。
自动调度依赖 GitHub Actions，5分钟计划可能延迟；未接入独立调度器。

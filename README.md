# GitHub Trending Tracker

自动追踪 GitHub Trending 热门项目，按兴趣标签过滤，生成中文总结。

## 功能

- 📅 **每日推送** — 自动抓取 GitHub Trending，过滤推荐项目
- 📊 **周报/月报** — 汇总分析，趋势洞察
- 🏷️ **兴趣标签** — 按你的方向精准推荐
- 🇨🇳 **中文总结** — 每个项目都有中文简介
- 🔄 **去重机制** — 只推新项目，不重复打扰

## 兴趣方向

| 标签 | 说明 |
|------|------|
| 边缘AI | 嵌入式/移动端AI推理 |
| AI部署 | 模型部署、推理优化 |
| AI Infra | MLOps、GPU集群、分布式训练 |
| AI Agent | 自主Agent、多智能体编排 |
| Vibe Coding | AI编程助手、Cursor/Copilot生态 |
| AI编程提效 | 代码生成、测试、重构 |
| 投资交易 | 量化交易、金融AI |
| AI for Science | AI加速科研 |

## 文件结构

```
├── daily/          # 每日报告
├── weekly/         # 周报
├── monthly/        # 月报
├── data/           # 原始JSON数据 + 去重记录
└── scripts/        # 抓取和分析脚本
```

## 定时任务

| 任务 | 时间 (北京时间) | 说明 |
|------|----------------|------|
| 每日抓取 | 每天 09:00 | 抓取 + 过滤 + 中文总结 |
| 周报 | 每周日 10:00 | 汇总7天 + 趋势分析 |
| 月报 | 每月1号 10:00 | 汇总30天 + 深度趋势 |

## 本地同步（Obsidian）

推荐使用 [Obsidian Git](https://github.com/denolehov/obsidian-git) 插件自动同步到本地 Obsidian vault。

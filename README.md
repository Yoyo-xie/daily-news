# 每日资讯热点

> 中文 AI 资讯热点聚合站。每天早 7 点自动抓取 11 个国内平台的热搜 + AI 筛选 + 卡片展示。

**🌐 在线访问：** [https://yoyo-xie.github.io/daily-news/](https://yoyo-xie.github.io/daily-news/)

![favicon](static/favicon-128x128.png)

## ✨ 特点

- **11 个中文平台**：抖音 / 微博 / 知乎 / 36氪 / 虎嗅 / 凤凰网 / 财新 / 华尔街见闻 等
- **AI 智能筛选**：Qwen-plus 按关注主题（地缘政治 / 大模型 / 金融市场等）自动挑选 + 生成今日导读
- **每天 7:00 自动更新**：GitHub Actions 定时跑，部署到 GitHub Pages
- **信息密集热榜视觉**：三栏布局 + 排名号 + 来源色 chip + 热度条 + 实时频率 sparkline，浅色/深色双主题

## 🛠 技术栈

- 上游框架：[TrendRadar](https://github.com/sansan0/TrendRadar)（爬虫 + AI 筛选 + RSS）
- AI 接入：Qwen-plus（通过 DashScope 兼容模式）
- 部署：GitHub Actions + GitHub Pages
- 自定义模板：`trendradar/report/html_aihot.py`（方案A · 信息密集热榜）

## 📂 项目结构

```
.
├── trendradar/             # 上游代码（爬虫、AI、报告生成）
│   └── report/
│       └── html_aihot.py   # 本项目的自定义视觉模板
├── config/                 # 抓取平台 + AI 关键词配置
├── static/                 # 网站静态资源（favicon 等）
├── .github/workflows/
│   └── crawler.yml         # 每日自动抓取 + 部署
├── README-TrendRadar.md    # 上游 TrendRadar 完整文档
└── README.md               # 本文件
```

## 🙏 致谢

本项目基于 [sansan0/TrendRadar](https://github.com/sansan0/TrendRadar) 二次开发，遵循其 GPL-3.0 协议。感谢上游作者提供的优秀框架。

## 📄 License

[GPL-3.0](LICENSE)（继承自上游 TrendRadar）

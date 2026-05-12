# daily-news 项目说明

## 这是什么

基于开源项目 [sansan0/TrendRadar](https://github.com/sansan0/TrendRadar) 改造的中文热点资讯聚合站，对标 [aihot.virxact.com](https://aihot.virxact.com) 的视觉设计。

- **公开网站**：https://yoyo-xie.github.io/daily-news/
- **GitHub 仓库**：https://github.com/Yoyo-xie/daily-news
- **本地路径**：`D:\Projects\TrendRadar`

## 工作流概览

```
GitHub Actions cron（每天北京时间 7:00）
  → 跑 trendradar 抓 11 个中国平台热榜
  → Qwen-plus AI 智能筛选 / 深度分析 / 翻译
  → 生成 HTML（AIHOT 风格深色 / 浅色双主题）
  → 自动部署到 GitHub Pages
朋友访问 → 永远是最新的内容
```

## 关键自定义文件（这些是我们的改造，**不要**轻易动）

| 文件 | 作用 |
|------|------|
| `trendradar/report/html_aihot.py` | **核心自定义模板**——AIHOT 风格的卡片化 feed 渲染器（约 500 行）。改样式 / 改文案 / 改布局都在这里 |
| `trendradar/report/__init__.py` | 第 22 行改成 `from trendradar.report.html_aihot import render_html_content`，绕过原 `html.py` |
| `.github/workflows/crawler.yml` | 每天 7am 跑 + 部署 Pages（用 `actions/upload-pages-artifact` + `actions/deploy-pages`）|
| `config/config.yaml` | 平台配置 / AI 模型配置。**API key 字段必须留空**（由 GH Secrets 注入）|
| `config/ai_interests.txt` | AI 自动提炼的兴趣标签（首次运行生成，可手动编辑）|
| `config/frequency_words.txt` | 关键词频次匹配（传统过滤）|
| `.gitignore` | 排除 `output/`、`__pycache__/` 等 |

**原始 `trendradar/report/html.py` 保留不动**，方便回滚。要回滚到原始紫色模板，只改 `__init__.py` 第 22 行的 import 即可。

## 视觉规则（避免下次走弯路）

- **图标全部用 inline SVG**，不用 emoji（emoji 在深色极简风格里显得不专业）
- **字体用系统栈**，不挂 Google Fonts：`ui-sans-serif, system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif`
- 颜色变量精确复刻 AIHOT 真实 CSS：
  - 深色：bg `#060814` / `#111827`，accent `#22d3ee`，text `#f1f5f9`
  - 浅色：bg `#fafbfc` / `#ffffff`，accent `#0891b2`，text `#0f172a`
- Hero 标题 "精选" 用 **font-weight: 300（细体）**，不要粗体
- Pill tabs 是**连体胶囊容器**（所有 tab 包在一个圆角容器里），不是分散胶囊
- 时间戳左侧大字 + 卡片右侧布局，时间用 `--time-color`（深色模式白，浅色模式深灰）
- "推荐理由" 已删除（TrendRadar 没有逐条 AI 点评数据，硬塞反而难看）
- Logo 是 `资讯 ⊙ 热点`（中间 SVG 圆点 + cyan 发光阴影）

## 侧边栏导航

7 项可点击切换视图（用 JS，无路由）：
- 精选 / 全部动态 / 每日日报（聚焦深度分析）/ 关于 / 更新日志 / 反馈
- 底部有**浅色 ↔ 深色切换按钮**，选择存 localStorage

## GitHub Secrets（已配，不要在代码里裸放）

| Name | Value（仅供本地测试参考）|
|------|--------|
| `AI_API_KEY` | Qwen DashScope key（本地存放路径见 `D:/Personal/book_translator/.env` 的 `DASHSCOPE_API_KEY`）|
| `AI_MODEL` | `openai/qwen-plus` |
| `AI_API_BASE` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

## 本地测试跑法

```powershell
cd D:/Projects/TrendRadar
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"
$env:AI_API_KEY="<从 D:/Personal/book_translator/.env 读 DASHSCOPE_API_KEY>"
$env:AI_MODEL="openai/qwen-plus"
$env:AI_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
uv run python -m trendradar
```

输出在 `output/html/latest/current.html`，浏览器打开预览。

## 部署流程（任何改动）

```bash
cd D:/Projects/TrendRadar
git add -A
git commit -m "描述改动"
git push
```

push 触发 GH Actions，2-3 分钟后线上更新。手动触发：https://github.com/Yoyo-xie/daily-news/actions

## 已踩的坑（避免重复）

1. **不要把上游 sansan0/TrendRadar 的 git 历史 push 上去**——里面有示例 webhook 被 GitHub secret scanning 拦截。当前仓库是 orphan branch 单 commit。
2. **README.md / README-EN.md 里 Slack webhook 示例**已改成 `<TEAM_ID>/<CHANNEL_ID>/<TOKEN>` 占位符，不要改回 `T00000000/B00000000/XX...`，会被扫描器拦。
3. **不要本地直接 schtasks 定时**——上次试了 `TrendRadarDaily` 任务，后来删了，全部走 GH Actions。
4. **不要往 config.yaml 写真实 API key**——公开仓库会泄漏，已设为空字符串走 env var。
5. **Python 版本**：GitHub Actions 用 3.12（pyproject.toml `requires-python = ">=3.12"`），本地是 3.14 也能跑。
6. **Telegram 推送已禁用**（`notification.enabled: false`），life_bot 的每日英语推送也注释了。

## 用户偏好（来自历史对话）

- 不写代码，全靠 Claude Code 生成
- 决策类问题先给立场判断，不要只列方案
- 回复合并成一条
- 产出文件后用 explorer 弹出文件夹，不要只打印路径

## 当前未完成 / 可改进项

- 字体在 Windows 上会回退到微软雅黑，跟 Mac 看 AIHOT 的苹方有差距。如果用户后续抱怨字体，方案：引入 HarmonyOS Sans SC 或 MiSans 的 CDN
- 卡片头像目前用 source name 首字符 + 青绿渐变圆，挺好。若再优化可以加平台 logo
- "每日日报"视图目前只是聚焦到 AI 分析区，并不是真正的"日报"形态。若要做成微信公号样式的日报，需要新模板
- 现在没做 SEO / OG 标签，朋友圈分享时缩略图丑

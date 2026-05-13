# coding=utf-8
"""
AIHOT 风格 HTML 报告渲染模块（深色版）

视觉对标 aihot.virxact.com：
- 左侧固定导航栏
- 主区域 hero + 胶囊式分类 tab
- 时间戳 + 卡片 feed
- 深色背景 + 青色高亮
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from trendradar.report.helpers import html_escape
from trendradar.ai.formatter import render_ai_analysis_html_rich


CSS = r"""
/* 颜色对齐 aihot.virxact.com 的主题变量 */
:root, [data-theme="dark"] {
    --bg-primary: #060814;
    --bg-secondary: #0b0f1a;
    --bg-card: #111827;
    --bg-card-hover: #1e293b;
    --bg-elevated: #1e293b;
    --bg-rec: rgba(255, 255, 255, 0.04);
    --border: rgba(255, 255, 255, 0.06);
    --border-soft: rgba(255, 255, 255, 0.04);
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent: #22d3ee;
    --accent-dim: #67e8f9;
    --accent-glow: rgba(34, 211, 238, 0.16);
    --accent-bg: rgba(34, 211, 238, 0.08);
    --time-color: #f1f5f9;
    --warn: #fbbf24;
    --danger: #fb7185;
    --card-shadow: none;
}

[data-theme="light"] {
    color-scheme: light;
    --bg-primary: #fafbfc;
    --bg-secondary: #f1f4f8;
    --bg-card: #ffffff;
    --bg-card-hover: #f5f7fa;
    --bg-elevated: #eef1f5;
    --bg-rec: rgba(15, 23, 42, 0.025);
    --border: rgba(15, 23, 42, 0.08);
    --border-soft: rgba(15, 23, 42, 0.05);
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --accent: #0891b2;
    --accent-dim: #155e75;
    --accent-glow: rgba(8, 145, 178, 0.12);
    --accent-bg: rgba(8, 145, 178, 0.06);
    --time-color: #0f172a;
    --warn: #b45309;
    --danger: #be123c;
    --card-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 23, 42, 0.06);
}

html { transition: background-color 0.25s ease; }
body { transition: background-color 0.25s ease, color 0.25s ease; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body {
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                 "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                 "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 15px;
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}
a { color: inherit; text-decoration: none; }

/* Layout */
.layout { display: flex; min-height: 100vh; }
.sidebar {
    width: 220px;
    flex-shrink: 0;
    padding: 24px 18px;
    border-right: 1px solid var(--border-soft);
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
}
.main { flex: 1; min-width: 0; padding: 32px 40px 80px; }

/* Sidebar logo */
.logo-box {
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px 14px;
    text-align: center;
    margin-bottom: 24px;
    background: var(--bg-secondary);
}
.logo-text {
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 0.02em;
    color: var(--text-primary);
    display: inline-flex;
    align-items: center;
    gap: 8px;
    line-height: 1;
}
.logo-icon {
    width: 20px;
    height: 20px;
    color: var(--accent);
    filter: drop-shadow(0 0 6px rgba(45, 212, 212, 0.5));
}

/* Theme toggle */
.theme-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    margin-top: 18px;
    padding: 10px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text-secondary);
    font-size: 13px;
    cursor: pointer;
    user-select: none;
    transition: all 0.15s ease;
    width: 100%;
}
.theme-toggle:hover { color: var(--text-primary); border-color: var(--accent-dim); }
.theme-toggle svg { width: 16px; height: 16px; stroke: currentColor; fill: none; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.theme-toggle .icon-sun { display: none; }
.theme-toggle .icon-moon { display: inline-block; }
[data-theme="light"] .theme-toggle .icon-sun { display: inline-block; }
[data-theme="light"] .theme-toggle .icon-moon { display: none; }
.theme-toggle .label-dark { display: none; }
.theme-toggle .label-light { display: inline; }
[data-theme="light"] .theme-toggle .label-dark { display: inline; }
[data-theme="light"] .theme-toggle .label-light { display: none; }

/* Sidebar nav */
.nav-list { display: flex; flex-direction: column; gap: 2px; }
.nav-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 14px;
    border-radius: 10px;
    color: var(--text-secondary);
    font-size: 13.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    border: 1px solid transparent;
    user-select: none;
    letter-spacing: 0.01em;
}
.nav-link:hover { background: var(--bg-card); color: var(--text-primary); }
.nav-link.active {
    background: var(--accent-bg);
    color: var(--accent);
    border-color: var(--accent-dim);
    box-shadow: 0 0 0 1px var(--accent-glow);
}
.nav-link svg {
    width: 17px;
    height: 17px;
    stroke: currentColor;
    fill: none;
    stroke-width: 1.6;
    stroke-linecap: round;
    stroke-linejoin: round;
    flex-shrink: 0;
}
.nav-link.active svg { stroke-width: 1.8; }

/* Hero */
.hero { margin-bottom: 32px; }
.hero-title {
    font-size: 34px;
    font-weight: 300;
    letter-spacing: 0.01em;
    color: var(--text-primary);
    margin-bottom: 8px;
    line-height: 1.25;
}
.hero-subtitle {
    font-size: 13.5px;
    color: var(--text-muted);
    letter-spacing: 0.02em;
    font-weight: 300;
}

/* Stat bar */
.stats-bar {
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
    padding: 14px 18px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    flex-wrap: wrap;
}
.stat-item { font-size: 12.5px; color: var(--text-muted); }
.stat-item b { color: var(--text-primary); font-weight: 600; font-size: 13px; }
.stat-divider { width: 1px; background: var(--border); }

/* Pill tabs — 连体胶囊容器 */
.pill-tabs-wrap {
    margin-bottom: 32px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
}
.pill-tabs {
    display: inline-flex;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 4px;
    gap: 2px;
}
.pill-tab {
    padding: 8px 22px;
    border-radius: 999px;
    border: 1px solid transparent;
    color: var(--text-secondary);
    font-size: 13.5px;
    font-weight: 400;
    cursor: pointer;
    background: transparent;
    transition: all 0.18s ease;
    user-select: none;
    white-space: nowrap;
}
.pill-tab:hover { color: var(--text-primary); }
.pill-tab.active {
    background: var(--accent-bg);
    color: var(--accent);
    border-color: var(--accent);
    box-shadow: 0 0 12px var(--accent-glow);
    font-weight: 500;
}
.pill-tab .count {
    font-size: 11px;
    margin-left: 6px;
    opacity: 0.65;
}

/* Editor note */
.editor-note {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    padding: 18px 22px;
    margin-bottom: 28px;
    border-radius: 0 10px 10px 0;
}
.editor-note-label {
    font-size: 11px;
    color: var(--accent);
    font-weight: 600;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.editor-note-content {
    font-size: 14px;
    line-height: 1.8;
    color: var(--text-secondary);
    white-space: pre-wrap;
}

/* Feed cards */
.feed { display: flex; flex-direction: column; }
.feed-item {
    display: flex;
    padding: 16px 0;
    border-bottom: 1px solid var(--border-soft);
    align-items: flex-start;
}
.feed-item .news-card { flex: 1; min-width: 0; }
.feed-item.hidden { display: none; }

.news-card {
    flex: 1;
    min-width: 0;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: var(--card-shadow);
    transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}
.news-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent-dim);
}
.card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 13px;
    color: var(--text-muted);
    flex-wrap: wrap;
}
.source-avatar {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-dim), var(--accent));
    color: #0a1119;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 700;
    flex-shrink: 0;
}
.source-name {
    color: var(--text-secondary);
    font-weight: 500;
}
.rank-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    background: rgba(245, 158, 11, 0.12);
    color: var(--warn);
    font-size: 11px;
    font-weight: 600;
}
.rank-badge.top { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
.rank-badge.high { background: rgba(245, 181, 81, 0.15); color: var(--time-color); }
.new-flag {
    background: rgba(45, 212, 212, 0.15);
    color: var(--accent);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
}
.repeat-flag {
    color: var(--text-muted);
    font-size: 11px;
}
.card-time {
    margin-left: auto;
    color: var(--text-muted);
    font-size: 11px;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    cursor: default;
}

.card-title {
    font-size: 16px;
    font-weight: 600;
    line-height: 1.5;
    margin-bottom: 8px;
    color: var(--text-primary);
}
.card-title a:hover { color: var(--accent); }

.card-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 10px;
}
.card-tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    background: var(--accent-bg);
    color: var(--accent);
    font-size: 11px;
    font-weight: 500;
}

.card-rec {
    margin-top: 12px;
    padding: 10px 14px;
    background: var(--bg-rec);
    border-radius: 6px;
    font-size: 12.5px;
    line-height: 1.65;
    color: var(--text-secondary);
}
.card-rec .label {
    color: var(--accent);
    font-weight: 600;
    margin-right: 6px;
}

/* Section header */
.section-header {
    font-size: 17px;
    font-weight: 700;
    margin: 40px 0 16px;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-header::before {
    content: "";
    display: inline-block;
    width: 3px;
    height: 16px;
    background: var(--accent);
    border-radius: 2px;
}

/* AI analysis */
.ai-analysis {
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 28px;
    border-radius: 12px;
    margin-top: 32px;
}
.ai-analysis h2 {
    font-size: 18px;
    margin-bottom: 18px;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 10px;
}
.ai-analysis h3 {
    font-size: 14px;
    color: var(--accent);
    margin: 20px 0 8px;
    font-weight: 600;
}
.ai-analysis h4 {
    font-size: 13px;
    color: var(--text-secondary);
    margin: 14px 0 6px;
    font-weight: 600;
}
.ai-analysis p, .ai-analysis li {
    font-size: 14px;
    line-height: 1.8;
    color: var(--text-secondary);
}
.ai-analysis p { margin-bottom: 10px; }
.ai-analysis ul, .ai-analysis ol { margin: 8px 0 12px 22px; }
.ai-analysis li { margin-bottom: 4px; }
.ai-analysis strong { color: var(--text-primary); font-weight: 600; }
.ai-analysis code {
    background: var(--bg-elevated);
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 13px;
    color: var(--accent);
}
.ai-analysis blockquote {
    border-left: 3px solid var(--accent-dim);
    padding: 4px 14px;
    color: var(--text-muted);
    margin: 12px 0;
}

/* Errors */
.error-section {
    background: rgba(245, 158, 11, 0.08);
    border-left: 3px solid var(--warn);
    padding: 12px 16px;
    margin-bottom: 24px;
    border-radius: 0 8px 8px 0;
    font-size: 13px;
    color: var(--warn);
}

/* Footer */
.site-footer {
    margin-top: 60px;
    padding-top: 24px;
    border-top: 1px solid var(--border-soft);
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
}

.empty-state { padding: 80px 20px; text-align: center; color: var(--text-muted); font-size: 14px; }

/* Responsive */
@media (max-width: 768px) {
    .layout { flex-direction: column; }
    .sidebar {
        width: 100%;
        height: auto;
        position: static;
        border-right: none;
        border-bottom: 1px solid var(--border-soft);
        padding: 16px;
    }
    .nav-list {
        flex-direction: row;
        overflow-x: auto;
        gap: 6px;
        -webkit-overflow-scrolling: touch;
    }
    .nav-link { flex-shrink: 0; }
    .logo-box { margin-bottom: 14px; padding: 10px; }
    .logo-text { font-size: 18px; }
    .main { padding: 20px 16px 60px; }
    .hero-title { font-size: 24px; }
    .news-card { padding: 14px 16px; }
}
"""


JS = r"""
function applyFilter(tabKey) {
    document.querySelectorAll('.pill-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabKey));
    document.querySelectorAll('.feed-item').forEach(item => {
        const tags = (item.dataset.tags || '').split('|').filter(Boolean);
        const type = item.dataset.type || '';
        let show = false;
        if (tabKey === 'all') show = true;
        else if (tabKey === 'hotlist' || tabKey === 'rss') show = (type === tabKey);
        else show = tags.includes(tabKey);
        item.classList.toggle('hidden', !show);
    });
}

function switchView(viewKey) {
    document.querySelectorAll('.nav-link').forEach(n => n.classList.toggle('active', n.dataset.view === viewKey));
    const hero = document.querySelector('.hero-title');
    const subtitle = document.querySelector('.hero-subtitle');
    const subtitleText = subtitle.dataset.base || subtitle.textContent;
    subtitle.dataset.base = subtitleText;

    const feed = document.querySelector('.feed');
    const pills = document.querySelector('.pill-tabs-wrap');
    const aiSection = document.querySelector('.ai-analysis');
    const editorNote = document.querySelector('.editor-note');

    if (viewKey === 'curated') {
        hero.textContent = '精选';
        subtitle.textContent = 'AI 自动挑选的全网高价值热点 · ' + subtitleText.split('·').slice(1).join('·').trim();
        if (feed) feed.style.display = '';
        if (pills) pills.style.display = '';
        if (editorNote) editorNote.style.display = '';
        if (aiSection) aiSection.style.display = '';
        applyFilter('all');
    } else if (viewKey === 'all') {
        hero.textContent = '全部动态';
        subtitle.textContent = '不做筛选的全量热点列表 · ' + subtitleText.split('·').slice(1).join('·').trim();
        if (feed) feed.style.display = '';
        if (pills) pills.style.display = '';
        if (editorNote) editorNote.style.display = '';
        if (aiSection) aiSection.style.display = 'none';
        applyFilter('all');
    } else if (viewKey === 'daily') {
        hero.textContent = '每日日报';
        subtitle.textContent = 'AI 对今日热点的深度分析与判断 · ' + subtitleText.split('·').slice(1).join('·').trim();
        if (feed) feed.style.display = 'none';
        if (pills) pills.style.display = 'none';
        if (editorNote) editorNote.style.display = 'none';
        if (aiSection) {
            aiSection.style.display = '';
            aiSection.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    } else if (viewKey === 'about') {
        hero.textContent = '关于';
        subtitle.textContent = '基于 TrendRadar 改造的资讯热点聚合工具';
        if (feed) feed.style.display = 'none';
        if (pills) pills.style.display = 'none';
        if (editorNote) editorNote.style.display = 'none';
        if (aiSection) aiSection.style.display = 'none';
    } else if (viewKey === 'changelog') {
        hero.textContent = '更新日志';
        subtitle.textContent = '本地报告暂不展示更新日志';
        if (feed) feed.style.display = 'none';
        if (pills) pills.style.display = 'none';
        if (editorNote) editorNote.style.display = 'none';
        if (aiSection) aiSection.style.display = 'none';
    } else if (viewKey === 'feedback') {
        hero.textContent = '反馈';
        subtitle.textContent = '需要调整？告诉 Claude Code 你的想法';
        if (feed) feed.style.display = 'none';
        if (pills) pills.style.display = 'none';
        if (editorNote) editorNote.style.display = 'none';
        if (aiSection) aiSection.style.display = 'none';
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('theme', theme); } catch (e) {}
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    setTheme(current === 'dark' ? 'light' : 'dark');
}
(function initTheme() {
    let saved;
    try { saved = localStorage.getItem('theme'); } catch (e) {}
    setTheme(saved || 'dark');
})();

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.pill-tab').forEach(tab => {
        tab.addEventListener('click', () => applyFilter(tab.dataset.tab));
    });
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => switchView(link.dataset.view));
    });
    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.addEventListener('click', toggleTheme);
});
"""


def _rank_class(min_rank: int, threshold: int = 10) -> str:
    if min_rank <= 3:
        return "top"
    if min_rank <= threshold:
        return "high"
    return ""


def _format_rank(ranks: List[int]) -> str:
    if not ranks:
        return ""
    mn, mx = min(ranks), max(ranks)
    return str(mn) if mn == mx else f"{mn}-{mx}"


def _make_recommendation(item: Dict, tags: List[str]) -> str:
    """根据数据特征生成"推荐理由"——基于多源命中/排名/标签，不调用额外 AI"""
    reasons = []
    ranks = item.get("ranks", [])
    count = item.get("count", 1)
    is_new = item.get("is_new", False)

    if ranks and min(ranks) <= 3:
        reasons.append(f"登顶 Top {min(ranks)}")
    elif ranks and min(ranks) <= 10:
        reasons.append("热度榜单前列")

    if count > 1:
        reasons.append(f"被多次上榜 ({count} 次)")

    if is_new:
        reasons.append("本轮新出现")

    if len(tags) >= 2:
        reasons.append(f"命中多个关注标签 ({len(tags)} 个)")
    elif len(tags) == 1:
        reasons.append(f"匹配标签：{tags[0]}")

    if not reasons:
        return ""

    return "、".join(reasons) + "。"


def _avatar_char(source: str) -> str:
    """从来源名抽取首字符做头像"""
    if not source:
        return "•"
    return source[0]


def _format_card_time(item: Dict) -> tuple:
    """返回 (短显示 HH:MM, 完整 tooltip)。RSS 用 published_at，热榜用 first_time。"""
    pub = item.get("published_at", "") or ""
    if pub:
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            return dt.strftime("%H:%M"), dt.strftime("%Y-%m-%d %H:%M") + "（发布时间）"
        except (ValueError, TypeError):
            pass

    td = item.get("time_display", "") or ""
    if td:
        first = td.strip("[]").split("~")[0].strip()
        if first:
            return first[:5], f"首次上榜 {first[:5]}"

    ft = item.get("first_time", "") or ""
    if ft:
        short = ft.replace("-", ":")[:5]
        return short, f"首次上榜 {short}"

    return "", ""


def _render_feed_item(
    item: Dict,
    tags: List[str],
    source_type: str,
) -> str:
    """渲染单条 feed 项"""
    title = html_escape(item.get("title", ""))
    url = item.get("mobile_url") or item.get("url", "")
    source_name = item.get("source_name", "")
    is_new = item.get("is_new", False)
    ranks = item.get("ranks", [])
    rank_threshold = item.get("rank_threshold", 10)
    count = item.get("count", 1)

    # 卡片头：头像 + 来源 + rank/new flags
    header_parts = []
    if source_name:
        header_parts.append(
            f'<span class="source-avatar">{html_escape(_avatar_char(source_name))}</span>'
            f'<span class="source-name">{html_escape(source_name)}</span>'
        )

    if is_new:
        header_parts.append('<span class="new-flag">NEW</span>')

    if count > 1:
        header_parts.append(f'<span class="repeat-flag">{count} 次上榜</span>')

    time_short, time_full = _format_card_time(item)
    if time_short:
        header_parts.append(
            f'<span class="card-time" title="{html_escape(time_full)}">{html_escape(time_short)}</span>'
        )

    header_html = "".join(header_parts)

    # 标题
    if url:
        title_html = (
            f'<a href="{html_escape(url)}" target="_blank" rel="noopener">{title}</a>'
        )
    else:
        title_html = title

    # 标签
    tag_html = ""
    if tags:
        chips = "".join(
            f'<span class="card-tag">{html_escape(t)}</span>' for t in tags
        )
        tag_html = f'<div class="card-tags">{chips}</div>'

    tags_data = html_escape("|".join(tags))

    return f"""
    <div class="feed-item" data-type="{source_type}" data-tags="{tags_data}">
        <article class="news-card">
            <div class="card-header">{header_html}</div>
            <div class="card-title">{title_html}</div>
            {tag_html}
        </article>
    </div>"""


def _deduplicate(stats: List[Dict], source_type: str) -> List[Dict]:
    """合并相同标题，累积所有命中的关键词作为 tags"""
    seen: Dict[str, Dict] = {}
    for stat in stats:
        keyword = stat.get("word", "")
        for title_data in stat.get("titles", []):
            key = title_data.get("title", "") + "|" + title_data.get("source_name", "")
            if key in seen:
                if keyword and keyword not in seen[key]["_tags"]:
                    seen[key]["_tags"].append(keyword)
            else:
                item = dict(title_data)
                item["_tags"] = [keyword] if keyword else []
                item["_source_type"] = source_type
                seen[key] = item
    return list(seen.values())


def render_html_content(
    report_data: Dict,
    total_titles: int,
    mode: str = "daily",
    update_info: Optional[Dict] = None,
    *,
    region_order: Optional[List[str]] = None,
    get_time_func: Optional[Callable[[], datetime]] = None,
    rss_items: Optional[List[Dict]] = None,
    rss_new_items: Optional[List[Dict]] = None,
    display_mode: str = "keyword",
    standalone_data: Optional[Dict] = None,
    ai_analysis: Optional[Any] = None,
    show_new_section: bool = True,
) -> str:
    """渲染深色 AIHOT 风格 HTML"""

    now = get_time_func() if get_time_func else datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # 扁平化
    hot_cards = _deduplicate(report_data.get("stats", []) or [], "hotlist")
    rss_cards = _deduplicate(rss_items or [], "rss")

    hot_count = len(hot_cards)
    rss_count = len(rss_cards)

    # tab 收集
    tab_data: Dict[str, int] = {}
    for stat in report_data.get("stats", []) or []:
        word = stat.get("word", "")
        if word:
            tab_data[word] = tab_data.get(word, 0) + len(stat.get("titles", []))

    # 排序卡片：先按是否有排名，再按排名升序
    def sort_key(item: Dict) -> tuple:
        ranks = item.get("ranks", [])
        return (min(ranks) if ranks else 999,)

    hot_cards_sorted = sorted(hot_cards, key=sort_key)

    # 渲染卡片
    card_parts = []
    for item in hot_cards_sorted:
        card_parts.append(_render_feed_item(item, item.get("_tags", []), "hotlist"))
    for item in rss_cards:
        card_parts.append(_render_feed_item(item, item.get("_tags", []), "rss"))
    feed_html = "".join(card_parts) or '<div class="empty-state">暂无内容</div>'

    # 失败提示
    failed_html = ""
    failed = report_data.get("failed_ids", []) or []
    if failed:
        failed_html = (
            '<div class="error-section">抓取失败的平台：'
            + ", ".join(html_escape(x) for x in failed)
            + "</div>"
        )

    # 编辑导读
    editor_note_html = ""
    if ai_analysis and getattr(ai_analysis, "success", False):
        core = (getattr(ai_analysis, "core_trends", "") or "").strip()
        if core:
            first_para = core.split("\n\n")[0].strip()
            if len(first_para) > 360:
                first_para = first_para[:360] + "…"
            editor_note_html = f"""
        <div class="editor-note">
            <div class="editor-note-label">今日导读</div>
            <div class="editor-note-content">{html_escape(first_para)}</div>
        </div>"""

    # Pill tabs
    pills = [
        f'<button class="pill-tab active" data-tab="all">全部<span class="count">{hot_count + rss_count}</span></button>',
        f'<button class="pill-tab" data-tab="hotlist">热榜<span class="count">{hot_count}</span></button>',
    ]
    if rss_count:
        pills.append(
            f'<button class="pill-tab" data-tab="rss">RSS<span class="count">{rss_count}</span></button>'
        )
    for word, cnt in sorted(tab_data.items(), key=lambda x: -x[1])[:6]:
        pills.append(
            f'<button class="pill-tab" data-tab="{html_escape(word)}">{html_escape(word)}'
            f'<span class="count">{cnt}</span></button>'
        )
    pills_html = '<div class="pill-tabs-wrap"><div class="pill-tabs">' + "".join(pills) + "</div></div>"

    # AI 分析
    ai_section_html = ""
    if ai_analysis and getattr(ai_analysis, "success", False):
        try:
            ai_rich = render_ai_analysis_html_rich(ai_analysis)
        except Exception:
            ai_rich = ""
        if ai_rich:
            ai_section_html = f"""
        <section class="ai-analysis">
            <h2>今日深度分析</h2>
            {ai_rich}
        </section>"""

    mode_label = {
        "daily": "全天汇总",
        "current": "实时榜单",
        "incremental": "增量更新",
    }.get(mode, mode)

    # SVG 图标（lucide style，单色线条）
    icon_logo = '<svg class="logo-icon" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="3.2" fill="currentColor"/></svg>'
    icon_zap = '<svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
    icon_list = '<svg viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><circle cx="3.5" cy="6" r="0.5" fill="currentColor"/><circle cx="3.5" cy="12" r="0.5" fill="currentColor"/><circle cx="3.5" cy="18" r="0.5" fill="currentColor"/></svg>'
    icon_file = '<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>'
    icon_plug = '<svg viewBox="0 0 24 24"><path d="M9 2v6"/><path d="M15 2v6"/><path d="M7 8h10v3a5 5 0 0 1-5 5 5 5 0 0 1-5-5V8z"/><path d="M12 16v6"/></svg>'
    icon_heart = '<svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>'
    icon_history = '<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/></svg>'
    icon_chat = '<svg viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>'

    icon_moon = '<svg class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    icon_sun = '<svg class="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.07" y2="4.93"/></svg>'

    sidebar_html = f"""
        <div class="logo-box">
            <div class="logo-text">资讯{icon_logo}热点</div>
        </div>
        <nav class="nav-list">
            <div class="nav-link active" data-view="curated">{icon_zap}精选</div>
            <div class="nav-link" data-view="all">{icon_list}全部动态</div>
            <div class="nav-link" data-view="daily">{icon_file}每日日报</div>
            <div class="nav-link" data-view="about">{icon_heart}关于</div>
            <div class="nav-link" data-view="changelog">{icon_history}更新日志</div>
            <div class="nav-link" data-view="feedback">{icon_chat}反馈</div>
        </nav>
        <div class="theme-toggle" id="themeToggle">
            {icon_moon}{icon_sun}
            <span class="label-light">浅色模式</span>
            <span class="label-dark">深色模式</span>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>资讯热点 · {date_str}</title>
    <script>(function(){{try{{var t=localStorage.getItem('theme')||'dark';document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}}})();</script>
    <style>{CSS}</style>
</head>
<body>
    <div class="layout">
        <aside class="sidebar">{sidebar_html}</aside>
        <main class="main">
            <div class="hero">
                <h1 class="hero-title">精选</h1>
                <div class="hero-subtitle">AI 自动挑选的全网高价值热点 · {date_str} · {time_str} · {mode_label}</div>
            </div>

            {failed_html}

            {editor_note_html}

            {pills_html}

            <div class="feed">{feed_html}</div>

            {ai_section_html}

            <footer class="site-footer">
                资讯热点 · 数据由 TrendRadar 抓取 · {now.strftime("%Y-%m-%d %H:%M:%S")}
            </footer>
        </main>
    </div>
    <script>{JS}</script>
</body>
</html>"""

    return html

# coding=utf-8
"""
方案A · 信息密集热榜 HTML 渲染模块

视觉对标"信息密集热榜"设计稿（Hacker News × 知乎热榜）：
- 三栏栅格：200px sidebar / 主区 / 280px right rail
- 浅色主题为主，保留深色切换
- 红色 brand，rank 1/2/3 颜色分级
- 每条 row：rank + source chip + category + NEW + time + 标题 + preview + 热度条/评论/趋势
"""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from trendradar.report.helpers import html_escape
from trendradar.ai.formatter import render_ai_analysis_html_rich

CSS = r"""
:root, [data-theme="light"] {
    color-scheme: light;
    /* Surface */
    --bg-page:       #fafaf9;
    --bg-card:       #ffffff;
    --bg-hover:      #fef2f2;
    --bg-feature:    linear-gradient(180deg, #fef2f2 0%, transparent 100%);
    --bg-soft:       #f5f5f4;
    /* Border */
    --border-strong: #e7e5e4;
    --border-soft:   #f5f5f4;
    /* Text */
    --text-1: #171717;
    --text-2: #404040;
    --text-3: #525252;
    --text-4: #737373;
    --text-5: #a8a29e;
    /* Brand & Heat */
    --brand:      #dc2626;
    --brand-bg:   #fef2f2;
    --brand-ring: rgba(220, 38, 38, 0.08);
    --brand-soft: #fee2e2;
    --rank-1: #dc2626;
    --rank-2: #ea580c;
    --rank-3: #d97706;
    --rank-r: #9ca3af;
    --trend-up:   #dc2626;
    --trend-down: #0891b2;
    --trend-flat: #9ca3af;
}

[data-theme="dark"] {
    color-scheme: dark;
    --bg-page:       #0a0a0a;
    --bg-card:       #171717;
    --bg-hover:      #1f1414;
    --bg-feature:    linear-gradient(180deg, rgba(220,38,38,0.10) 0%, transparent 100%);
    --bg-soft:       #1f1f1f;
    --border-strong: #262626;
    --border-soft:   #1f1f1f;
    --text-1: #fafafa;
    --text-2: #e5e5e5;
    --text-3: #d4d4d4;
    --text-4: #a3a3a3;
    --text-5: #737373;
    --brand-bg:   #2a0e0e;
    --brand-ring: rgba(220, 38, 38, 0.18);
    --brand-soft: #3a1414;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
html { transition: background-color 0.25s ease; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei",
                 "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg-page);
    color: var(--text-1);
    font-size: 13px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
    transition: background-color 0.25s ease, color 0.25s ease;
}
a { color: inherit; text-decoration: none; }
button { font-family: inherit; }

.mono {
    font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, "SF Mono",
                 Menlo, Consolas, monospace;
    font-variant-numeric: tabular-nums;
}
.serif {
    font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC",
                 "STSong", serif;
}

/* ====== Layout ====== */
.layout {
    display: grid;
    grid-template-columns: 200px 1fr 280px;
    min-height: 100vh;
}

/* ====== Sidebar ====== */
.sidebar {
    background: var(--bg-card);
    border-right: 1px solid var(--border-strong);
    padding: 20px 14px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
}
.brand { display: flex; align-items: center; gap: 10px; padding: 4px 6px; }
.brand-mark {
    width: 34px; height: 34px; border-radius: 8px;
    background: var(--brand); color: #fff;
    display: grid; place-items: center;
    font-weight: 800; font-size: 18px;
    font-family: "Noto Serif SC", "Source Han Serif SC", serif;
    flex-shrink: 0;
}
.brand-name { font-weight: 700; font-size: 14px; letter-spacing: 0.5px; color: var(--text-1); }
.brand-sub  { font-size: 10px; color: var(--text-5); letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }

.nav-list { display: flex; flex-direction: column; gap: 1px; }
.nav-link {
    display: flex; align-items: center; gap: 10px;
    padding: 7px 8px; border-radius: 6px;
    color: var(--text-3); font-size: 13px;
    cursor: pointer; position: relative;
    transition: background-color 0.15s ease, color 0.15s ease;
    user-select: none;
}
.nav-link:hover { background: var(--bg-soft); color: var(--text-1); }
.nav-link.active { background: var(--brand-bg); color: var(--brand); font-weight: 600; }
.nav-link.active::after {
    content: ""; position: absolute; right: 8px;
    width: 5px; height: 5px; border-radius: 99px; background: var(--brand);
}
.nav-icon { width: 14px; text-align: center; font-size: 12px; flex-shrink: 0; }

.sidebar-section { margin-top: 4px; }
.sidebar-label {
    font-size: 10px; font-weight: 700;
    color: var(--text-5); letter-spacing: 2px;
    padding: 4px 8px 10px;
    text-transform: uppercase;
}
.src-row {
    display: flex; align-items: center; gap: 8px;
    padding: 5px 8px; font-size: 12px;
}
.src-dot { width: 6px; height: 6px; border-radius: 99px; flex-shrink: 0; }
.src-name { flex: 1; color: var(--text-2); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.src-count { font-size: 10px; color: var(--text-5); }

.theme-toggle {
    margin-top: auto;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    padding: 8px 10px;
    border: 1px solid var(--border-strong);
    border-radius: 6px;
    background: var(--bg-card);
    color: var(--text-3);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
}
.theme-toggle:hover { color: var(--text-1); border-color: var(--text-5); }
.theme-toggle svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.theme-toggle .icon-sun  { display: none; }
.theme-toggle .icon-moon { display: inline-block; }
[data-theme="dark"] .theme-toggle .icon-sun  { display: inline-block; }
[data-theme="dark"] .theme-toggle .icon-moon { display: none; }
.theme-toggle .label-dark  { display: inline; }
.theme-toggle .label-light { display: none; }
[data-theme="dark"] .theme-toggle .label-light { display: inline; }
[data-theme="dark"] .theme-toggle .label-dark  { display: none; }

/* ====== Main ====== */
.main { min-width: 0; display: flex; flex-direction: column; }

/* Header */
.main-header {
    display: flex; justify-content: space-between; align-items: flex-end;
    padding: 22px 28px 14px;
    border-bottom: 1px solid var(--border-soft);
    gap: 12px;
    flex-wrap: wrap;
}
.hero-h1 {
    font-size: 28px; font-weight: 800;
    letter-spacing: -0.5px; line-height: 1.1;
    color: var(--text-1);
    margin: 0;
}
.hero-date {
    font-size: 14px; font-weight: 400; color: var(--text-5);
    margin-left: 4px;
}
.hero-sub {
    display: flex; gap: 10px; align-items: center;
    margin-top: 6px; font-size: 12px; color: var(--text-4);
    flex-wrap: wrap;
}
.hero-sub b { color: var(--text-1); font-weight: 600; }
.hero-sub .up { color: var(--brand); }
.live {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 10px; font-weight: 700;
    color: var(--brand); letter-spacing: 1px;
}
.live-dot {
    width: 6px; height: 6px; border-radius: 99px;
    background: var(--brand);
    box-shadow: 0 0 0 3px var(--brand-soft);
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 3px var(--brand-soft); }
    50%      { box-shadow: 0 0 0 5px rgba(220, 38, 38, 0.25); }
}

.header-actions { display: flex; gap: 6px; }
.btn {
    padding: 6px 10px;
    border: 1px solid var(--border-strong);
    background: var(--bg-card);
    border-radius: 6px;
    font-size: 12px;
    color: var(--text-3);
    cursor: pointer;
    transition: all 0.15s ease;
}
.btn:hover { border-color: var(--text-5); color: var(--text-1); }
.btn-primary {
    padding: 6px 12px;
    border: 1px solid var(--brand);
    background: var(--brand);
    color: #fff;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
}
.btn-primary:hover { background: #b91c1c; border-color: #b91c1c; }

/* Category strip */
.cat-strip {
    display: flex; gap: 4px;
    padding: 12px 28px;
    border-bottom: 1px solid var(--border-soft);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
.cat-strip::-webkit-scrollbar { height: 0; }
.cat {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 11px;
    border: 1px solid var(--border-strong);
    border-radius: 99px;
    font-size: 12px;
    color: var(--text-3);
    background: var(--bg-card);
    cursor: pointer;
    transition: all 0.18s ease;
    white-space: nowrap;
    user-select: none;
}
.cat:hover { color: var(--text-1); }
.cat.active {
    font-weight: 600;
    box-shadow: 0 0 0 3px var(--brand-ring);
}
.cat-num {
    font-size: 10px;
    color: var(--text-5);
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
}

/* ====== News Rows ====== */
.feed { padding: 4px 0 20px; }
.feed-item {
    display: flex;
    gap: 14px;
    padding: 14px 28px;
    border-bottom: 1px solid var(--border-soft);
    cursor: pointer;
    transition: background-color 0.12s ease;
    align-items: flex-start;
}
.feed-item:hover { background: var(--bg-hover); }
.feed-item.is-first { background: var(--bg-feature); }
.feed-item.is-first:hover { background: var(--bg-hover); }
.feed-item.hidden { display: none; }

.row-rank {
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-size: 22px;
    font-weight: 800;
    width: 38px;
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
    text-align: right;
    padding-top: 2px;
    flex-shrink: 0;
}
.row-rank.r1 { color: var(--rank-1); }
.row-rank.r2 { color: var(--rank-2); }
.row-rank.r3 { color: var(--rank-3); }
.row-rank.rr { color: var(--rank-r); }

.row-body { flex: 1; min-width: 0; }
.row-meta-top {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 4px;
    font-size: 11px;
    flex-wrap: wrap;
}
.src-chip {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 1px 8px;
    border: 1px solid;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.55;
}
.src-chip-dot { width: 5px; height: 5px; border-radius: 99px; flex-shrink: 0; }
.cat-tag {
    font-size: 11px;
    color: var(--text-4);
}
.new-tag {
    font-size: 9px;
    font-weight: 800;
    color: var(--brand);
    background: var(--brand-soft);
    padding: 1px 5px;
    border-radius: 3px;
    letter-spacing: 0.5px;
}
.repeat-tag {
    font-size: 10px;
    color: var(--text-5);
    font-family: "JetBrains Mono", ui-monospace, monospace;
}
.row-time {
    margin-left: auto;
    font-size: 11px;
    color: var(--text-5);
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
    cursor: default;
}

.row-title {
    font-size: 15px;
    font-weight: 700;
    margin: 2px 0 4px;
    line-height: 1.35;
    color: var(--text-1);
}
.row-title a:hover { color: var(--brand); }
.row-preview {
    font-size: 12.5px;
    color: var(--text-4);
    margin: 0 0 8px;
    line-height: 1.55;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.row-preview.empty { display: none; }

.row-meta-bot { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.heat-wrap { display: flex; align-items: center; gap: 8px; flex: 1; max-width: 340px; min-width: 140px; }
.heat-bar  { flex: 1; height: 4px; background: var(--bg-soft); border-radius: 99px; overflow: hidden; }
.heat-fill { height: 100%; border-radius: 99px; transition: width 300ms ease; }
.heat-fill.r1 { background: var(--rank-1); }
.heat-fill.r2 { background: var(--rank-2); }
.heat-fill.r3 { background: var(--rank-3); }
.heat-fill.rr { background: var(--rank-r); }
.heat-num {
    font-size: 11px;
    font-weight: 700;
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
.heat-num.r1 { color: var(--rank-1); }
.heat-num.r2 { color: var(--rank-2); }
.heat-num.r3 { color: var(--rank-3); }
.heat-num.rr { color: var(--rank-r); }

.meta-stats {
    display: flex; gap: 14px;
    font-size: 11px;
    color: var(--text-4);
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
}
.trend-up   { color: var(--trend-up);   font-weight: 600; }
.trend-down { color: var(--trend-down); font-weight: 600; }
.trend-flat { color: var(--trend-flat); font-weight: 600; }

.empty-state { padding: 80px 20px; text-align: center; color: var(--text-5); font-size: 14px; }

/* ====== Right rail ====== */
.right-rail {
    background: var(--bg-card);
    border-left: 1px solid var(--border-strong);
    padding: 20px 18px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
}
.panel { }
.panel-title {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 12px; font-weight: 700;
    color: var(--text-1);
    margin-bottom: 10px;
}
.panel-more { font-size: 10px; color: var(--text-5); font-weight: 400; cursor: pointer; }

.heat-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 12px; }
.heat-row-num {
    width: 14px;
    font-family: "JetBrains Mono", ui-monospace, monospace;
    font-size: 11px; font-weight: 700;
    color: var(--text-5);
}
.heat-row-mid { flex: 1; min-width: 0; }
.heat-row-name {
    font-size: 12px; color: var(--text-2);
    margin-bottom: 3px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.heat-row-bar-bg { height: 3px; background: var(--bg-soft); border-radius: 99px; overflow: hidden; }
.heat-row-bar    { height: 100%; background: linear-gradient(90deg, #f97316, #dc2626); border-radius: 99px; }
.heat-row-count  {
    font-size: 10px;
    color: var(--text-5);
    font-family: "JetBrains Mono", ui-monospace, monospace;
}

.brief { display: flex; flex-direction: column; gap: 6px; font-size: 11.5px; color: var(--text-3); line-height: 1.6; }
.brief-line { display: flex; gap: 6px; }
.brief-bullet { color: var(--brand); font-weight: 700; flex-shrink: 0; }
.brief b { color: var(--text-1); font-weight: 700; }

.spark { display: flex; gap: 2px; height: 48px; align-items: flex-end; }
.spark-bar { flex: 1; border-radius: 1px; min-height: 2px; background: #cbd5e1; }
.spark-bar.recent { background: var(--brand); }
.spark-foot {
    display: flex; justify-content: space-between;
    font-size: 9px; color: var(--text-5);
    margin-top: 4px;
    font-family: "JetBrains Mono", ui-monospace, monospace;
}

/* ====== AI Analysis ====== */
.ai-analysis {
    margin: 24px 28px 32px;
    background: var(--bg-card);
    border: 1px solid var(--border-strong);
    padding: 24px 28px;
    border-radius: 10px;
}
.ai-analysis h2 {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 16px;
    color: var(--text-1);
    display: flex; align-items: center; gap: 10px;
}
.ai-analysis h2::before {
    content: ""; width: 3px; height: 14px;
    background: var(--brand); border-radius: 2px;
}
.ai-analysis h3 { font-size: 13px; color: var(--brand); margin: 16px 0 6px; font-weight: 700; }
.ai-analysis h4 { font-size: 12px; color: var(--text-3); margin: 12px 0 4px; font-weight: 600; }
.ai-analysis p, .ai-analysis li { font-size: 13px; line-height: 1.75; color: var(--text-3); }
.ai-analysis p { margin-bottom: 8px; }
.ai-analysis ul, .ai-analysis ol { margin: 6px 0 10px 20px; }
.ai-analysis li { margin-bottom: 3px; }
.ai-analysis strong { color: var(--text-1); font-weight: 700; }
.ai-analysis code {
    background: var(--bg-soft);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 12px;
    color: var(--brand);
    font-family: "JetBrains Mono", ui-monospace, monospace;
}
.ai-analysis blockquote {
    border-left: 3px solid var(--brand);
    padding: 4px 14px;
    color: var(--text-4);
    margin: 10px 0;
}

/* Errors */
.error-section {
    margin: 14px 28px 0;
    background: rgba(245, 158, 11, 0.08);
    border-left: 3px solid #d97706;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    font-size: 12px;
    color: #b45309;
}
[data-theme="dark"] .error-section { color: #fbbf24; background: rgba(251, 191, 36, 0.06); }

/* Footer */
.site-footer {
    margin-top: 32px;
    padding: 18px 28px;
    border-top: 1px solid var(--border-soft);
    text-align: center;
    font-size: 11px;
    color: var(--text-5);
    font-family: "JetBrains Mono", ui-monospace, monospace;
}

/* ====== Responsive ====== */
@media (max-width: 1280px) {
    .layout { grid-template-columns: 200px 1fr; }
    .right-rail { display: none; }
}
@media (max-width: 1024px) {
    .layout { grid-template-columns: 180px 1fr; }
}
@media (max-width: 768px) {
    .layout { grid-template-columns: 1fr; }
    .sidebar {
        position: static; height: auto;
        border-right: none;
        border-bottom: 1px solid var(--border-strong);
        flex-direction: column;
        padding: 14px;
        gap: 14px;
    }
    .nav-list { flex-direction: row; flex-wrap: wrap; gap: 4px; }
    .nav-link { padding: 6px 10px; }
    .sidebar-section { display: none; }
    .theme-toggle { margin-top: 0; }
    .main-header { padding: 18px 16px 12px; }
    .hero-h1 { font-size: 22px; }
    .cat-strip { padding: 10px 16px; }
    .feed-item { padding: 14px 16px; gap: 10px; }
    .row-rank { width: 28px; font-size: 18px; }
    .row-preview { display: none; }
    .row-meta-bot { gap: 8px; }
    .heat-wrap { max-width: none; }
    .ai-analysis { margin: 18px 16px; padding: 16px; }
    .site-footer { padding: 14px 16px; }
}
"""


JS = r"""
function applyFilter(tabKey) {
    document.querySelectorAll('.cat').forEach(t => t.classList.toggle('active', t.dataset.tab === tabKey));
    let visibleIdx = 0;
    document.querySelectorAll('.feed-item').forEach(item => {
        const tags = (item.dataset.tags || '').split('|').filter(Boolean);
        const type = item.dataset.type || '';
        let show = false;
        if (tabKey === 'all') show = true;
        else if (tabKey === 'hotlist' || tabKey === 'rss') show = (type === tabKey);
        else show = tags.includes(tabKey);
        item.classList.toggle('hidden', !show);
        item.classList.remove('is-first');
        if (show && visibleIdx === 0) {
            item.classList.add('is-first');
            visibleIdx++;
        } else if (show) {
            visibleIdx++;
        }
    });
}

function switchView(viewKey) {
    document.querySelectorAll('.nav-link').forEach(n => n.classList.toggle('active', n.dataset.view === viewKey));
    const h1 = document.querySelector('.hero-h1');
    const date = document.querySelector('.hero-date');
    const subtitle = document.querySelector('.hero-sub-meta');
    const dateBase = date ? date.dataset.base || date.textContent : '';
    if (date) date.dataset.base = dateBase;

    const feed = document.querySelector('.feed');
    const cats = document.querySelector('.cat-strip');
    const rail = document.querySelector('.right-rail');
    const aiSection = document.querySelector('.ai-analysis');

    const setMain = (mainText) => { if (h1) h1.firstChild.nodeValue = mainText + ' '; };

    if (viewKey === 'curated') {
        setMain('热榜');
        if (feed) feed.style.display = '';
        if (cats) cats.style.display = '';
        if (rail) rail.style.display = '';
        if (aiSection) aiSection.style.display = '';
        applyFilter('all');
    } else if (viewKey === 'all') {
        setMain('全部动态');
        if (feed) feed.style.display = '';
        if (cats) cats.style.display = '';
        if (rail) rail.style.display = '';
        if (aiSection) aiSection.style.display = 'none';
        applyFilter('all');
    } else if (viewKey === 'daily') {
        setMain('每日日报');
        if (feed) feed.style.display = 'none';
        if (cats) cats.style.display = 'none';
        if (rail) rail.style.display = 'none';
        if (aiSection) {
            aiSection.style.display = '';
            aiSection.scrollIntoView({behavior:'smooth', block:'start'});
        }
    } else if (viewKey === 'about') {
        setMain('关于');
        if (feed) feed.style.display = 'none';
        if (cats) cats.style.display = 'none';
        if (rail) rail.style.display = 'none';
        if (aiSection) aiSection.style.display = 'none';
    } else if (viewKey === 'changelog') {
        setMain('更新日志');
        if (feed) feed.style.display = 'none';
        if (cats) cats.style.display = 'none';
        if (rail) rail.style.display = 'none';
        if (aiSection) aiSection.style.display = 'none';
    } else if (viewKey === 'feedback') {
        setMain('反馈');
        if (feed) feed.style.display = 'none';
        if (cats) cats.style.display = 'none';
        if (rail) rail.style.display = 'none';
        if (aiSection) aiSection.style.display = 'none';
    }
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('theme', theme); } catch (e) {}
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    setTheme(current === 'light' ? 'dark' : 'light');
}
(function initTheme() {
    let saved;
    try { saved = localStorage.getItem('theme'); } catch (e) {}
    setTheme(saved || 'light');
})();

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.cat').forEach(tab => {
        tab.addEventListener('click', () => applyFilter(tab.dataset.tab));
    });
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => switchView(link.dataset.view));
    });
    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.addEventListener('click', toggleTheme);
});
"""


# ====== 数据兜底辅助 ======

# 已知来源品牌色
_SOURCE_COLORS: Dict[str, str] = {
    "抖音": "#000000",
    "微博": "#E6162D",
    "微博热搜": "#E6162D",
    "知乎": "#0066FF",
    "36氪": "#0A8060",
    "36kr": "#0A8060",
    "虎嗅": "#F4A300",
    "凤凰网": "#D7263D",
    "凤凰": "#D7263D",
    "财新": "#C8102E",
    "网易": "#C8102E",
    "网易新闻": "#C8102E",
    "百度": "#2932E1",
    "百度热搜": "#2932E1",
    "B站": "#FB7299",
    "哔哩哔哩": "#FB7299",
    "今日头条": "#FF3B30",
    "头条": "#FF3B30",
    "澎湃": "#DE0000",
    "澎湃新闻": "#DE0000",
    "央视": "#C8000A",
    "央视新闻": "#C8000A",
    "第一财经": "#B71C1C",
    "钛媒体": "#FF6B35",
    "量子位": "#7C3AED",
    "21世纪经济": "#0033A0",
    "21财经": "#0033A0",
    "华尔街见闻": "#1A3A7E",
    "贴吧": "#2E7BFF",
    "GitHub": "#181717",
    "Hacker News": "#FF6600",
    "hackernews": "#FF6600",
    "新浪": "#E60012",
    "新浪新闻": "#E60012",
    "新浪财经": "#E60012",
    "腾讯": "#0052D9",
    "腾讯新闻": "#0052D9",
    "搜狐": "#FF6F00",
    "雪球": "#1E90FF",
    "少数派": "#D14B47",
}

_FALLBACK_PALETTE = [
    "#0891b2", "#a855f7", "#f59e0b", "#dc2626", "#0ea5e9",
    "#10b981", "#6366f1", "#ef4444", "#737373",
]


def _src_color(source: str) -> str:
    if not source:
        return _FALLBACK_PALETTE[0]
    if source in _SOURCE_COLORS:
        return _SOURCE_COLORS[source]
    # 子串匹配
    for k, v in _SOURCE_COLORS.items():
        if k and (k in source or source in k):
            return v
    # 哈希兜底
    h = hashlib.md5(source.encode("utf-8")).digest()[0]
    return _FALLBACK_PALETTE[h % len(_FALLBACK_PALETTE)]


def _hex_with_alpha(hex_color: str, alpha_hex: str) -> str:
    """支持 #RRGGBB → 加上 alpha 字段；alpha 是 2 位 hex 字符串"""
    c = hex_color.strip()
    if c.startswith("#") and len(c) == 7:
        return c + alpha_hex
    return c


def _rank_bucket(min_rank: int) -> str:
    if min_rank <= 1:
        return "r1"
    if min_rank == 2:
        return "r2"
    if min_rank == 3:
        return "r3"
    return "rr"


def _synth_heat(min_rank: int) -> int:
    """根据排名合成热度数值（兜底，用于排序条宽度和显示）"""
    if min_rank <= 0:
        min_rank = 1
    # 1→990k, 2→980k, 10→900k, 50→500k, 100→0
    val = max(0, (100 - min_rank)) * 10000
    return val


def _heat_pct(heat: int) -> float:
    """0-100% 用于条形宽度"""
    return max(2.0, min(100.0, heat / 10000.0))


def fmt_heat(n: int) -> str:
    if n >= 10000:
        return f"{n/10000:.1f}w"
    if n >= 1000:
        return f"{n/1000:.1f}k"
    return str(n)


def _synth_trend(item: Dict) -> tuple:
    """返回 (key, display)"""
    count = item.get("count", 1) or 1
    is_new = item.get("is_new", False)
    ranks = item.get("ranks", []) or []
    if count >= 3:
        return "up", f"↑ +{min(count * 8, 99)}%"
    if is_new:
        return "up", "↑ NEW"
    if ranks and min(ranks) <= 3:
        return "up", "↑ 上升"
    return "flat", "→ 持平"


def _extract_preview(item: Dict, title: str) -> str:
    """从 summary / description 字段抽取预览；没有则空串。"""
    for k in ("summary", "description", "preview", "content_summary"):
        v = (item.get(k) or "").strip()
        if v:
            # 去 HTML 标签
            clean = re.sub(r"<[^>]+>", " ", v)
            clean = re.sub(r"\s+", " ", clean).strip()
            if clean and clean != title:
                return clean[:80] + ("…" if len(clean) > 80 else "")
    return ""


def _format_card_time(item: Dict) -> tuple:
    """返回 (HH:MM, tooltip)"""
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


def _extract_hour(item: Dict) -> Optional[int]:
    pub = item.get("published_at", "") or ""
    if pub:
        try:
            dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            return dt.hour
        except (ValueError, TypeError):
            pass
    td = item.get("time_display", "") or ""
    if td:
        m = re.search(r"(\d{2}):(\d{2})", td)
        if m:
            return int(m.group(1))
    ft = item.get("first_time", "") or ""
    if ft and ":" in ft:
        m = re.search(r"(\d{1,2})[:\-](\d{2})", ft)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None


# ====== 渲染 ======

def _render_feed_item(item: Dict, tags: List[str], source_type: str, idx: int) -> str:
    title = html_escape(item.get("title", ""))
    url = item.get("mobile_url") or item.get("url", "")
    source_name = item.get("source_name", "")
    is_new = item.get("is_new", False)
    ranks = item.get("ranks", []) or []
    count = item.get("count", 1) or 1
    min_rank = min(ranks) if ranks else 99

    rank_cls = _rank_bucket(min_rank)
    rank_label = f"{min_rank:02d}" if min_rank < 99 else "—"

    src_color = _src_color(source_name)
    src_chip_bg = _hex_with_alpha(src_color, "0d")
    src_chip_border = _hex_with_alpha(src_color, "40")

    cat_text = tags[0] if tags else ""
    time_short, time_full = _format_card_time(item)
    preview = _extract_preview(item, item.get("title", ""))

    heat = _synth_heat(min_rank)
    heat_pct = _heat_pct(heat)
    heat_disp = fmt_heat(heat)
    trend_key, trend_disp = _synth_trend(item)

    # 拼 meta-top
    parts = []
    if source_name:
        parts.append(
            f'<span class="src-chip" style="color:{src_color};border-color:{src_chip_border};background:{src_chip_bg};">'
            f'<span class="src-chip-dot" style="background:{src_color};"></span>'
            f'{html_escape(source_name)}</span>'
        )
    if cat_text:
        parts.append(f'<span class="cat-tag">{html_escape(cat_text)}</span>')
    if is_new:
        parts.append('<span class="new-tag">NEW</span>')
    if count > 1:
        parts.append(f'<span class="repeat-tag">×{count}</span>')
    if time_short:
        parts.append(f'<span class="row-time" title="{html_escape(time_full)}">{html_escape(time_short)}</span>')
    meta_top_html = "".join(parts)

    if url:
        title_html = f'<a href="{html_escape(url)}" target="_blank" rel="noopener">{title}</a>'
    else:
        title_html = title

    preview_cls = "row-preview" if preview else "row-preview empty"
    preview_html = html_escape(preview) if preview else ""

    first_cls = " is-first" if idx == 0 else ""
    tags_data = html_escape("|".join(tags))

    return f"""
    <div class="feed-item{first_cls}" data-type="{source_type}" data-tags="{tags_data}">
        <div class="row-rank {rank_cls}">{rank_label}</div>
        <div class="row-body">
            <div class="row-meta-top">{meta_top_html}</div>
            <h3 class="row-title">{title_html}</h3>
            <p class="{preview_cls}">{preview_html}</p>
            <div class="row-meta-bot">
                <div class="heat-wrap">
                    <div class="heat-bar"><div class="heat-fill {rank_cls}" style="width:{heat_pct:.1f}%;"></div></div>
                    <span class="heat-num {rank_cls}">🔥 {heat_disp}</span>
                </div>
                <div class="meta-stats">
                    <span class="trend-{trend_key}">{html_escape(trend_disp)}</span>
                </div>
            </div>
        </div>
    </div>"""


def _deduplicate(stats: List[Dict], source_type: str) -> List[Dict]:
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
    """渲染方案A · 信息密集热榜风格 HTML"""

    now = get_time_func() if get_time_func else datetime.now()
    date_dot = now.strftime("%Y.%m.%d")
    time_str = now.strftime("%H:%M")

    # 扁平化
    hot_cards = _deduplicate(report_data.get("stats", []) or [], "hotlist")
    rss_cards = _deduplicate(rss_items or [], "rss")

    hot_count = len(hot_cards)
    rss_count = len(rss_cards)
    total_count = hot_count + rss_count

    # 排序：先按排名升序
    def sort_key(item: Dict) -> tuple:
        ranks = item.get("ranks", []) or []
        return (min(ranks) if ranks else 999,)

    hot_cards_sorted = sorted(hot_cards, key=sort_key)
    rss_cards_sorted = sorted(rss_cards, key=sort_key)
    all_items = hot_cards_sorted + rss_cards_sorted

    # 重新计算 rank（合并后的 1-based 全局排名）
    for i, it in enumerate(all_items, start=1):
        it["_global_rank"] = i

    # 渲染每条 row（rank 用全局位置）
    card_parts = []
    for idx, item in enumerate(all_items):
        item_copy = dict(item)
        item_copy["ranks"] = [item["_global_rank"]]
        card_parts.append(_render_feed_item(item_copy, item.get("_tags", []), item.get("_source_type", "hotlist"), idx))
    feed_html = "".join(card_parts) or '<div class="empty-state">暂无内容</div>'

    # NEW 数量
    new_count = sum(1 for it in all_items if it.get("is_new"))

    # tab 收集（top 6 关键词）
    tab_data: Dict[str, int] = {}
    for item in all_items:
        for t in item.get("_tags", []) or []:
            tab_data[t] = tab_data.get(t, 0) + 1

    # 来源统计（前 5）
    source_counts: Dict[str, int] = {}
    for it in all_items:
        s = it.get("source_name", "") or ""
        if s:
            source_counts[s] = source_counts.get(s, 0) + 1
    top_sources = sorted(source_counts.items(), key=lambda x: -x[1])[:6]

    # 失败提示
    failed_html = ""
    failed = report_data.get("failed_ids", []) or []
    if failed:
        failed_html = (
            '<div class="error-section">抓取失败的平台：'
            + ", ".join(html_escape(x) for x in failed)
            + "</div>"
        )

    # 分类 chip
    cats = [
        f'<div class="cat active" data-tab="all">全部 <span class="cat-num">{total_count}</span></div>',
        f'<div class="cat" data-tab="hotlist">热榜 <span class="cat-num">{hot_count}</span></div>',
    ]
    if rss_count:
        cats.append(f'<div class="cat" data-tab="rss">RSS <span class="cat-num">{rss_count}</span></div>')
    for word, cnt in sorted(tab_data.items(), key=lambda x: -x[1])[:8]:
        cats.append(
            f'<div class="cat" data-tab="{html_escape(word)}">{html_escape(word)} '
            f'<span class="cat-num">{cnt}</span></div>'
        )
    cat_strip = '<div class="cat-strip">' + "".join(cats) + "</div>"

    # 右栏 - 热度 TOP 分类
    if tab_data:
        sorted_cats = sorted(tab_data.items(), key=lambda x: -x[1])[:5]
        max_cnt = max((c for _, c in sorted_cats), default=1)
        cat_rows = []
        for i, (name, cnt) in enumerate(sorted_cats):
            pct = max(8, int(cnt / max_cnt * 100))
            cat_rows.append(f"""
            <div class="heat-row">
                <span class="heat-row-num">{i+1}</span>
                <div class="heat-row-mid">
                    <div class="heat-row-name">{html_escape(name)}</div>
                    <div class="heat-row-bar-bg"><div class="heat-row-bar" style="width:{pct}%;"></div></div>
                </div>
                <span class="heat-row-count">{cnt}</span>
            </div>""")
        heat_top_html = "".join(cat_rows)
    else:
        heat_top_html = '<div style="font-size:11.5px;color:var(--text-5);padding:8px 0;">暂无分类数据</div>'

    # 右栏 - 今日导读
    brief_lines = []
    if ai_analysis and getattr(ai_analysis, "success", False):
        core = (getattr(ai_analysis, "core_trends", "") or "").strip()
        if core:
            paras = [p.strip() for p in core.split("\n") if p.strip()][:3]
            labels = ["宏观主线", "微观焦点", "情绪信号"]
            for i, p in enumerate(paras):
                clean = re.sub(r"<[^>]+>", "", p).strip()
                clean = re.sub(r"^[*#\-•·\d\.\s]+", "", clean)
                if len(clean) > 70:
                    clean = clean[:70] + "…"
                brief_lines.append(
                    f'<div class="brief-line"><span class="brief-bullet">—</span>'
                    f'<span><b>{labels[i] if i < len(labels) else ""}</b>　{html_escape(clean)}</span></div>'
                )
    if not brief_lines:
        brief_lines = [
            f'<div class="brief-line"><span class="brief-bullet">—</span>'
            f'<span><b>共 {total_count} 条</b>　覆盖 {len(source_counts)} 个来源</span></div>',
            f'<div class="brief-line"><span class="brief-bullet">—</span>'
            f'<span><b>新增动态</b>　本轮新出现 {new_count} 条 <span style="color:var(--brand);">↑</span></span></div>',
            f'<div class="brief-line"><span class="brief-bullet">—</span>'
            f'<span><b>分类热度</b>　{html_escape(sorted_cats[0][0]) if tab_data else "—"} 居首</span></div>',
        ]
    brief_html = "".join(brief_lines)

    # 右栏 - 实时频率 sparkline（24h 桶）
    buckets = [0] * 24
    for it in all_items:
        h = _extract_hour(it)
        if h is not None and 0 <= h <= 23:
            buckets[h] += 1
    if max(buckets) == 0:
        buckets = [1] * 24  # 占位
    bmax = max(buckets) or 1
    current_hour = now.hour
    bars = []
    for h in range(24):
        pct = max(4, int(buckets[h] / bmax * 100))
        is_recent = (h <= current_hour and h >= current_hour - 4) or (current_hour < 4 and h >= 20)
        cls = "spark-bar recent" if is_recent else "spark-bar"
        bars.append(f'<div class="{cls}" style="height:{pct}%;"></div>')
    spark_html = "".join(bars)

    # AI 详细分析
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

    # 订阅源面板
    src_rows = []
    for name, cnt in top_sources:
        color = _src_color(name)
        src_rows.append(
            f'<div class="src-row"><span class="src-dot" style="background:{color};"></span>'
            f'<span class="src-name" title="{html_escape(name)}">{html_escape(name)}</span>'
            f'<span class="src-count">{cnt}</span></div>'
        )
    src_panel = "".join(src_rows) or '<div style="font-size:11px;color:var(--text-5);padding:6px 8px;">暂无</div>'

    # SVG 图标（单色线条）
    icon_moon = '<svg class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    icon_sun  = '<svg class="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.07" y2="4.93"/></svg>'

    sidebar_html = f"""
        <div class="brand">
            <div class="brand-mark">日</div>
            <div>
                <div class="brand-name">每日资讯热点</div>
                <div class="brand-sub">DAILY HOTSPOTS</div>
            </div>
        </div>
        <nav class="nav-list">
            <div class="nav-link active" data-view="curated"><span class="nav-icon">★</span><span>精选</span></div>
            <div class="nav-link" data-view="all"><span class="nav-icon">≡</span><span>全部动态</span></div>
            <div class="nav-link" data-view="daily"><span class="nav-icon">▤</span><span>每日日报</span></div>
            <div class="nav-link" data-view="about"><span class="nav-icon">◌</span><span>关于</span></div>
            <div class="nav-link" data-view="changelog"><span class="nav-icon">↻</span><span>更新日志</span></div>
            <div class="nav-link" data-view="feedback"><span class="nav-icon">✎</span><span>反馈</span></div>
        </nav>
        <div class="sidebar-section">
            <div class="sidebar-label">订阅源</div>
            {src_panel}
        </div>
        <div class="theme-toggle" id="themeToggle">
            {icon_moon}{icon_sun}
            <span class="label-light">浅色模式</span>
            <span class="label-dark">深色模式</span>
        </div>"""

    right_rail_html = f"""
        <div class="panel">
            <div class="panel-title"><span>🔥 热度TOP分类</span><span class="panel-more">{html_escape(mode_label)}</span></div>
            {heat_top_html}
        </div>
        <div class="panel">
            <div class="panel-title"><span>📍 今日导读</span></div>
            <div class="brief">{brief_html}</div>
        </div>
        <div class="panel">
            <div class="panel-title"><span>⏱ 实时频率</span></div>
            <div class="spark">{spark_html}</div>
            <div class="spark-foot"><span>00:00</span><span>近24h</span><span>现在</span></div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日资讯热点 · {date_dot}</title>
    <script>(function(){{try{{var t=localStorage.getItem('theme')||'light';document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}}})();</script>
    <link rel="icon" href="favicon.ico" sizes="any">
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
    <link rel="manifest" href="site.webmanifest">
    <meta name="theme-color" content="#171717">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>{CSS}</style>
</head>
<body>
    <div class="layout">
        <aside class="sidebar">{sidebar_html}</aside>
        <main class="main">
            <header class="main-header">
                <div>
                    <h1 class="hero-h1">热榜 <span class="hero-date mono">· {date_dot}</span></h1>
                    <div class="hero-sub hero-sub-meta">
                        <span class="live"><span class="live-dot"></span>LIVE</span>
                        <span class="mono">{time_str} 更新</span>
                        <span>·</span>
                        <span>共 <b>{total_count}</b> 条</span>
                        <span>·</span>
                        <span>新增 <b class="up">↑ {new_count}</b></span>
                        <span>·</span>
                        <span>{html_escape(mode_label)}</span>
                    </div>
                </div>
                <div class="header-actions">
                    <button class="btn">⇅ 排序</button>
                    <button class="btn" onclick="location.reload()">↻ 刷新</button>
                </div>
            </header>

            {failed_html}

            {cat_strip}

            <div class="feed">{feed_html}</div>

            {ai_section_html}

            <footer class="site-footer">
                每日资讯热点 · 数据由 TrendRadar 抓取 · {now.strftime("%Y-%m-%d %H:%M:%S")}
            </footer>
        </main>
        <aside class="right-rail">{right_rail_html}</aside>
    </div>
    <script>{JS}</script>
</body>
</html>"""

    return html

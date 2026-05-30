"""为筛选后的新闻条目补抓封面图（og:image）。

热榜（newsnow）与 RSS 原始数据都不含图片字段，这里对进入展示的条目
逐个请求文章页，解析 <meta property="og:image"> / twitter:image，
写入 item["image_url"]。抓不到就跳过，卡片保持纯文字（优雅降级）。

只对筛选后的少量条目抓图（按排名取前 N 条），并发 + 超时 + 全程兜底，
不影响主流程：任何异常都只是少一张图。
"""

import concurrent.futures
import html as _html
import re
from typing import Dict, List
from urllib.parse import urljoin

import requests

# og:image / twitter:image 的 <meta> 两种属性顺序都要兼容
_OG_PATTERNS = [
    re.compile(r'<meta[^>]+property=["\']og:image(?::url)?["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::url)?["\']', re.I),
    re.compile(r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']', re.I),
    re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']', re.I),
]

# 视频平台：即使只抓到封面图，也在卡片上加播放角标（点击跳原页）
_VIDEO_KEYS = (
    "douyin", "抖音", "bilibili", "哔哩", "b站",
    "youtube", "youtu.be", "kuaishou", "快手", "tiktok", "/video",
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 占位图 / 默认 logo 关键词——抓到这类一律忽略（避免一堆雷同 logo 占满卡片）
_BAD_IMG_HINTS = (
    "logo", "default", "placeholder", "blank", "avatar", "favicon", "icon", "share.png", "share.jpg",
)

_MAX_BYTES = 200_000  # og 标签都在 <head>，读前 ~200KB 足够


def _item_url(item: Dict) -> str:
    return item.get("url") or item.get("mobileUrl") or item.get("mobile_url") or ""


def _is_video(item: Dict) -> bool:
    blob = ((item.get("source_name") or "") + " " + _item_url(item)).lower()
    return any(k in blob for k in _VIDEO_KEYS)


def _extract_og_image(page_html: str, base_url: str) -> str:
    for pat in _OG_PATTERNS:
        m = pat.search(page_html)
        if m:
            u = _html.unescape(m.group(1).strip())
            if not u:
                continue
            low = u.lower()
            if any(h in low for h in _BAD_IMG_HINTS):
                continue
            return urljoin(base_url, u)
    return ""


def _fetch_one(url: str, timeout: float) -> str:
    """抓单个页面的封面图，失败返回空串（绝不抛异常给上层）。"""
    try:
        with requests.get(
            url, headers=_HEADERS, timeout=timeout, stream=True, allow_redirects=True
        ) as resp:
            ctype = resp.headers.get("Content-Type", "").lower()
            if "html" not in ctype and "text" not in ctype and ctype:
                return ""
            # 注：不能在第一个 </head> 处停——不少站首屏是个小外壳，
            # 真正的 og 标签在后面注入，所以统一读到 _MAX_BYTES 上限。
            buf = b""
            for chunk in resp.iter_content(8192):
                if chunk:
                    buf += chunk
                if len(buf) >= _MAX_BYTES:
                    break
            page = buf.decode(resp.encoding or "utf-8", errors="ignore")
            return _extract_og_image(page, str(resp.url))
    except Exception:
        return ""


def enrich_groups_with_images(
    groups: List[Dict],
    *,
    max_items: int = 60,
    timeout: float = 6.0,
    max_workers: int = 8,
) -> None:
    """就地为 groups（[{word, titles:[item,...]}, ...]）里的 item 补 image_url / is_video。

    - 按最高排名优先，最多抓 max_items 条（0=不限制）。
    - 同一 url 的多个 item 共享抓取结果，去重抓取。
    """
    if not groups:
        return

    by_url: Dict[str, List[Dict]] = {}
    url_rank: Dict[str, int] = {}
    for g in groups:
        for it in g.get("titles", []) or []:
            it["is_video"] = _is_video(it)  # 视频标记与抓图无关，先打上
            # RSS feed 自带封面的条目直接跳过——不重复抓、不覆盖
            if it.get("image_url"):
                continue
            u = _item_url(it)
            if not u:
                continue
            ranks = it.get("ranks") or []
            r = min(ranks) if ranks else 999
            url_rank[u] = min(url_rank.get(u, 999), r)
            by_url.setdefault(u, []).append(it)

    if not by_url:
        return

    targets = sorted(by_url.keys(), key=lambda u: url_rank.get(u, 999))
    if max_items and max_items > 0:
        targets = targets[:max_items]

    found = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_fetch_one, u, timeout): u for u in targets}
        for fut in concurrent.futures.as_completed(futs):
            u = futs[fut]
            try:
                img = fut.result()
            except Exception:
                img = ""
            if img:
                for it in by_url.get(u, []):
                    it["image_url"] = img
                found += 1

    print(f"[配图] 目标 {len(targets)} 条，成功抓到封面 {found} 条")

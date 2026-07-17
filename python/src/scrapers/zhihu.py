"""知乎 AI 话题爬虫"""

from __future__ import annotations

from datetime import datetime, timezone

from bs4 import BeautifulSoup

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

# 知乎 AI 相关热榜/话题页
ZHIHU_HOT_URL = "https://www.zhihu.com/hot"
AI_KEYWORDS = ["AI", "人工智能", "大模型", "GPT", "Claude", "Llama", "机器学习", "深度学习"]


class ZhihuScraper(ScraperInterface):
    source = Source.ZHIHU

    async def scrape(self) -> list[RawIntelligence]:
        # 知乎需要 cookie 才能访问，这里提供基础框架
        # 实际使用时需要配置登录态
        items: list[RawIntelligence] = []

        try:
            resp = await self._client.get(
                ZHIHU_HOT_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Cookie": "",  # 需要配置知乎 cookie
                },
            )
            if resp.status_code != 200:
                return items

            soup = BeautifulSoup(resp.text, "html.parser")
            hot_items = soup.select(".HotList-item")

            for item in hot_items:
                title_tag = item.select_one(".HotList-itemTitle")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)

                # 过滤 AI 相关话题
                if not any(kw in title for kw in AI_KEYWORDS):
                    continue

                link_tag = item.select_one("a")
                url = link_tag.get("href", "") if link_tag else ""
                if url and not url.startswith("http"):
                    url = f"https://www.zhihu.com{url}"

                items.append(RawIntelligence(
                    source=self.source,
                    title=f"[知乎热榜] {title}",
                    url=url,
                    rawContent=f"知乎热榜: {title}",
                    publishedAt=datetime.now(timezone.utc).isoformat(),
                    language=Language.ZH,
                    metadata={},
                ))
        except Exception:
            pass

        return items

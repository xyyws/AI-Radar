"""微信公众号 AI 爬虫 — 通过 RSS 聚合服务采集"""

from __future__ import annotations

import feedparser

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

# 常用的微信公众号 RSS 聚合源（需要自行部署或使用第三方服务）
# 这里使用 WeRSS / feeddd 等公开聚合源作为示例
WECHAT_FEEDS = [
    # 用户需要自行配置 RSS 源地址
    # "https://rsshub.app/wechat/feeddd/xxx",
]


class WechatScraper(ScraperInterface):
    source = Source.WECHAT

    async def scrape(self) -> list[RawIntelligence]:
        if not WECHAT_FEEDS:
            return []

        items: list[RawIntelligence] = []
        for feed_url in WECHAT_FEEDS:
            try:
                resp = await self._client.get(feed_url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

                for entry in feed.entries[:15]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "")
                    summary = entry.get("summary", "").strip()
                    published = entry.get("published", "")

                    raw_content = f"微信公众号: {title}\n"
                    if summary:
                        raw_content += f"摘要: {summary[:2000]}\n"

                    items.append(RawIntelligence(
                        source=self.source,
                        title=title,
                        url=link,
                        rawContent=raw_content,
                        publishedAt=published,
                        language=Language.ZH,
                        metadata={"feed": feed_url},
                    ))
            except Exception:
                continue

        return items

"""OpenAI Blog 爬虫 — 使用 RSS"""

from __future__ import annotations

from datetime import datetime, timezone
from time import mktime

import feedparser

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

RSS_URL = "https://openai.com/blog/rss.xml"


class OpenAIBlogScraper(ScraperInterface):
    source = Source.OPENAI

    async def scrape(self) -> list[RawIntelligence]:
        resp = await self._client.get(RSS_URL)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)

        items: list[RawIntelligence] = []
        for entry in feed.entries[:15]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            summary = entry.get("summary", "").strip()

            published_parsed = entry.get("published_parsed")
            if published_parsed:
                published = datetime.fromtimestamp(
                    mktime(published_parsed), tz=timezone.utc
                ).isoformat()
            else:
                published = datetime.now(timezone.utc).isoformat()

            raw_content = f"OpenAI Blog: {title}\n"
            if summary:
                raw_content += f"Summary: {summary[:2000]}\n"

            items.append(RawIntelligence(
                source=self.source,
                title=title,
                url=link,
                rawContent=raw_content,
                publishedAt=published,
                language=Language.EN,
                metadata={},
            ))
        return items

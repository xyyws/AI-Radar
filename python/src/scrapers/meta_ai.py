"""Meta AI Blog 爬虫 — 使用 RSS + curl 兜底"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from time import mktime

import feedparser

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

RSS_URLS = [
    "https://ai.meta.com/blog/rss/",
    "https://ai.meta.com/feed/",
]


class MetaAIScraper(ScraperInterface):
    source = Source.META

    async def scrape(self) -> list[RawIntelligence]:
        feed_text = ""

        for url in RSS_URLS:
            try:
                resp = await self._client.get(url)
                if resp.status_code == 200 and len(resp.text) > 100:
                    feed_text = resp.text
                    break
            except Exception:
                continue

        if not feed_text:
            for url in RSS_URLS:
                try:
                    r = subprocess.run(
                        ["curl", "-sL", "--max-time", "15", url],
                        capture_output=True, text=True, timeout=20,
                    )
                    if r.returncode == 0 and len(r.stdout) > 100:
                        feed_text = r.stdout
                        break
                except Exception:
                    continue

        if not feed_text:
            return []

        feed = feedparser.parse(feed_text)
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

            raw_content = f"Meta AI: {title}\n"
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

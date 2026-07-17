"""Arxiv AI 论文爬虫 — 通过 RSS 采集 cs.AI / cs.LG / cs.CL 分类"""

from __future__ import annotations

from datetime import datetime, timezone
from time import mktime

import feedparser

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

# AI 相关分类的 RSS
ARXIV_FEEDS = [
    "https://export.arxiv.org/rss/cs.AI",   # Artificial Intelligence
    "https://export.arxiv.org/rss/cs.LG",   # Machine Learning
    "https://export.arxiv.org/rss/cs.CL",   # Computation and Language
]


class ArxivScraper(ScraperInterface):
    source = Source.ARXIV

    async def scrape(self) -> list[RawIntelligence]:
        items: list[RawIntelligence] = []

        for feed_url in ARXIV_FEEDS:
            resp = await self._client.get(feed_url)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

            for entry in feed.entries[:20]:  # 每个分类取前 20 篇
                title = entry.get("title", "").strip()
                link = entry.get("link", "")
                summary = entry.get("summary", "").strip()

                # 提取作者
                authors = ", ".join(
                    a.get("name", "") for a in entry.get("authors", [])
                )

                # 使用 feedparser 的 parsed 时间结构，避免 RFC 2822 解析问题
                published_parsed = entry.get("published_parsed")
                if published_parsed:
                    published = datetime.fromtimestamp(
                        mktime(published_parsed), tz=timezone.utc
                    ).isoformat()
                else:
                    published = datetime.now(timezone.utc).isoformat()

                raw_content = f"Title: {title}\n"
                if authors:
                    raw_content += f"Authors: {authors}\n"
                if summary:
                    raw_content += f"Abstract: {summary[:2000]}\n"

                evidence = []
                if authors:
                    evidence.append(f"作者: {authors[:100]}")
                if summary:
                    evidence.append(f"摘要: {summary[:200]}")
                evidence.append(f"分类: {feed_url.split('/')[-1]}")

                items.append(RawIntelligence(
                    source=self.source,
                    title=title,
                    url=link,
                    rawContent=raw_content,
                    publishedAt=published,
                    language=Language.EN,
                    metadata={"authors": authors, "feed": feed_url},
                    evidence=evidence,
                ))

        return items

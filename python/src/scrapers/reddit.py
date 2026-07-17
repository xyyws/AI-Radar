"""Reddit AI 社区爬虫 — 采集 r/MachineLearning, r/artificial 等"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

AI_SUBREDDITS = [
    "MachineLearning",
    "artificial",
    "LocalLLaMA",
    "singularity",
]


class RedditScraper(ScraperInterface):
    source = Source.REDDIT

    async def scrape(self) -> list[RawIntelligence]:
        items: list[RawIntelligence] = []

        for subreddit in AI_SUBREDDITS:
            try:
                # 使用 Reddit JSON API（无需认证）
                resp = await self._client.get(
                    f"https://www.reddit.com/r/{subreddit}/hot.json?limit=15",
                    headers={"User-Agent": "AI-Radar/0.1"},
                )
                if resp.status_code != 200:
                    continue

                posts = resp.json().get("data", {}).get("children", [])
                for post in posts:
                    data = post.get("data", {})
                    title = data.get("title", "")
                    selftext = data.get("selftext", "")[:2000]
                    url = f"https://reddit.com{data.get('permalink', '')}"
                    score = data.get("score", 0)
                    comments = data.get("num_comments", 0)
                    created = datetime.fromtimestamp(
                        data.get("created_utc", 0), tz=timezone.utc
                    ).isoformat()

                    raw_content = f"r/{subreddit}: {title}\n"
                    raw_content += f"Score: {score}, Comments: {comments}\n"
                    if selftext:
                        raw_content += f"Content: {selftext}\n"

                    evidence = [f"Score: {score}", f"Comments: {comments}"]

                    items.append(RawIntelligence(
                        source=self.source,
                        title=f"[r/{subreddit}] {title}",
                        url=url,
                        rawContent=raw_content,
                        publishedAt=created,
                        language=Language.EN,
                        evidence=evidence,
                        metadata={
                            "subreddit": subreddit,
                            "score": score,
                            "comments": comments,
                        },
                    ))
            except Exception:
                continue

        return items

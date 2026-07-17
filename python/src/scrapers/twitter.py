"""X (Twitter) AI 爬虫 — 通过 API 采集 AI 领域关键账号动态"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

# AI 领域关键账号（可通过配置扩展）
AI_ACCOUNTS = [
    "OpenAI",
    "AnthropicAI",
    "GoogleDeepMind",
    "MetaAI",
    "huggingface",
    "ylecun",
    "kaborez",
    "DrJimFan",
]


class TwitterScraper(ScraperInterface):
    source = Source.TWITTER

    async def scrape(self) -> list[RawIntelligence]:
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer_token:
            return []

        items: list[RawIntelligence] = []
        headers = {"Authorization": f"Bearer {bearer_token}"}

        for account in AI_ACCOUNTS:
            try:
                # 使用 Twitter API v2 用户时间线
                # 需要先获取 user_id
                user_resp = await self._client.get(
                    f"https://api.twitter.com/2/users/by/username/{account}",
                    headers=headers,
                )
                if user_resp.status_code != 200:
                    continue

                user_id = user_resp.json().get("data", {}).get("id")
                if not user_id:
                    continue

                tweets_resp = await self._client.get(
                    f"https://api.twitter.com/2/users/{user_id}/tweets",
                    headers=headers,
                    params={
                        "max_results": 10,
                        "tweet.fields": "created_at,text",
                    },
                )
                if tweets_resp.status_code != 200:
                    continue

                tweets = tweets_resp.json().get("data", [])
                for tweet in tweets:
                    text = tweet.get("text", "")
                    tweet_id = tweet.get("id", "")
                    created = tweet.get("created_at", datetime.now(timezone.utc).isoformat())

                    items.append(RawIntelligence(
                        source=self.source,
                        title=f"@{account}: {text[:80]}...",
                        url=f"https://x.com/{account}/status/{tweet_id}",
                        rawContent=f"@{account}: {text}",
                        publishedAt=created,
                        language=Language.EN,
                        metadata={"account": account, "tweet_id": tweet_id},
                    ))
            except Exception:
                continue

        return items

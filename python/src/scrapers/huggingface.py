"""HuggingFace Trending 爬虫 — 采集热门模型和数据集"""

from __future__ import annotations

from datetime import datetime, timezone

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

# HuggingFace API endpoints（国内镜像）
MODELS_API = "https://hf-mirror.com/api/models?sort=likes&direction=-1&limit=20"


class HuggingFaceScraper(ScraperInterface):
    source = Source.HUGGINGFACE

    async def scrape(self) -> list[RawIntelligence]:
        items: list[RawIntelligence] = []

        # 采集热门模型
        resp = await self._client.get(MODELS_API)
        resp.raise_for_status()
        models = resp.json()

        for model in models:
            model_id = model.get("id", "")
            url = f"https://huggingface.co/{model_id}"
            downloads = model.get("downloads", 0)
            likes = model.get("likes", 0)
            pipeline = model.get("pipeline_tag", "")
            tags = model.get("tags", [])

            raw_content = f"Model: {model_id}\n"
            if pipeline:
                raw_content += f"Task: {pipeline}\n"
            raw_content += f"Downloads: {downloads}\n"
            raw_content += f"Likes: {likes}\n"
            if tags:
                raw_content += f"Tags: {', '.join(tags[:10])}\n"

            evidence = []
            if downloads:
                evidence.append(f"下载量: {downloads}")
            if likes:
                evidence.append(f"点赞: {likes}")
            if pipeline:
                evidence.append(f"任务类型: {pipeline}")

            items.append(RawIntelligence(
                source=self.source,
                title=f"HuggingFace Model: {model_id}",
                url=url,
                rawContent=raw_content,
                publishedAt=datetime.now(timezone.utc).isoformat(),
                language=Language.EN,
                evidence=evidence,
                metadata={
                    "downloads": downloads,
                    "likes": likes,
                    "pipeline_tag": pipeline,
                },
            ))

        return items

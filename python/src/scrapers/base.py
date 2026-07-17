"""爬虫基类 — 所有数据源适配器必须实现此接口"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import httpx

from python.src.models.raw_intelligence import RawIntelligence, Source

logger = logging.getLogger(__name__)


class ScraperInterface(ABC):
    """数据源爬虫抽象基类

    每个数据源实现一个子类，实现 scrape() 方法。
    爬虫只负责采集和初步结构化，清洗逻辑交给 normalizer。
    """

    source: Source

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            trust_env=False,  # 绕过系统代理，避免 SSL 兼容问题
            headers={"User-Agent": "AI-Radar/0.1 (Intelligence Collector)"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    @abstractmethod
    async def scrape(self) -> list[RawIntelligence]:
        """采集数据源的原始情报

        Returns:
            符合 RawIntelligence 模型的情报列表

        Raises:
            httpx.HTTPError: 网络请求失败
            ValueError: 数据解析失败
        """
        ...

    async def safe_scrape(self) -> list[RawIntelligence]:
        """带容错的采集入口，单源失败不影响整体流程"""
        try:
            items = await self.scrape()
            logger.info(f"[{self.source.value}] 采集到 {len(items)} 条情报")
            return items
        except Exception as e:
            logger.error(f"[{self.source.value}] 采集失败: {e}")
            return []
        finally:
            await self.close()

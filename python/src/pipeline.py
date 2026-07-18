"""采集编排入口 — 并行调度所有爬虫，输出统一 JSON"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from python.src.cleaners.normalizer import normalize
from python.src.cleaners.intelligence_filter import select_top_intelligence
from python.src.cleaners.health_monitor import record_health
from python.src.models.raw_intelligence import RawIntelligence
from python.src.scrapers.github_trending import GitHubTrendingScraper
from python.src.scrapers.arxiv import ArxivScraper
from python.src.scrapers.openai_blog import OpenAIBlogScraper
from python.src.scrapers.anthropic_blog import AnthropicBlogScraper
from python.src.scrapers.deepmind import DeepMindScraper
from python.src.scrapers.meta_ai import MetaAIScraper
from python.src.scrapers.huggingface import HuggingFaceScraper
from python.src.scrapers.twitter import TwitterScraper
from python.src.scrapers.reddit import RedditScraper
from python.src.scrapers.wechat import WechatScraper
from python.src.scrapers.zhihu import ZhihuScraper
from python.src.scrapers.base import ScraperInterface

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 所有可用的爬虫注册表
SCRAPERS: dict[str, type[ScraperInterface]] = {
    "github": GitHubTrendingScraper,
    "arxiv": ArxivScraper,
    "openai": OpenAIBlogScraper,
    "anthropic": AnthropicBlogScraper,
    "deepmind": DeepMindScraper,
    "meta": MetaAIScraper,
    "huggingface": HuggingFaceScraper,
    "twitter": TwitterScraper,
    "reddit": RedditScraper,
    "wechat": WechatScraper,
    "zhihu": ZhihuScraper,
}


async def run_scraper(name: str, scraper_cls: type[ScraperInterface]) -> list[RawIntelligence]:
    """运行单个爬虫"""
    scraper = scraper_cls()
    return await scraper.safe_scrape()


async def run_pipeline(
    sources: list[str] | None = None,
    output_dir: str = "data/raw",
) -> Path:
    """执行完整的采集管道

    Args:
        sources: 要采集的数据源列表，None 表示全部
        output_dir: 输出目录

    Returns:
        输出文件路径
    """
    if sources is None:
        sources = list(SCRAPERS.keys())

    # 验证数据源
    invalid = [s for s in sources if s not in SCRAPERS]
    if invalid:
        raise ValueError(f"未知数据源: {invalid}. 可用: {list(SCRAPERS.keys())}")

    logger.info(f"开始采集，数据源: {sources}")

    # 分批执行爬虫（每批最多 3 个并发，避免撑爆代理）
    all_items: list[RawIntelligence] = []
    batch_size = 3
    for i in range(0, len(sources), batch_size):
        batch = sources[i:i + batch_size]
        tasks = [run_scraper(name, SCRAPERS[name]) for name in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                logger.error(f"[{name}] 采集异常: {result}")
            elif isinstance(result, list):
                all_items.extend(result)

    logger.info(f"采集完成，原始情报: {len(all_items)} 条")

    # 清洗
    raw_count = len(all_items)
    all_items = normalize(all_items)
    dedup_removed = raw_count - len(all_items)

    # 智能过滤：去重、评分、精选 top 30
    all_items = select_top_intelligence(all_items, max_items=30)

    # 输出 JSON
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = output_path / "radar_data.json"

    data = {
        "date": today,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "total_items": len(all_items),
        "items": [item.model_dump(by_alias=True) for item in all_items],
    }

    # 自定义 JSON 序列化，确保 datetime 输出标准 ISO 8601 格式（T 分隔符）
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat().replace(" ", "T")
        return str(obj)

    output_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=json_serializer),
        encoding="utf-8",
    )

    logger.info(f"数据已写入: {output_file}")

    # 记录健康指标
    health_file = Path(output_dir).parent / "health.json"
    health = record_health(all_items, raw_count, dedup_removed, health_file)
    if health.get("alerts"):
        logger.warning(f"健康报警: {len(health['alerts'])} 条异常")

    return output_file


def main() -> None:
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Radar 数据采集管道")
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(SCRAPERS.keys()),
        help="指定数据源（默认全部）",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw",
        help="输出目录（默认 data/raw）",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="列出所有可用数据源",
    )

    args = parser.parse_args()

    if args.list_sources:
        print("可用数据源:")
        for name in SCRAPERS:
            print(f"  - {name}")
        return

    asyncio.run(run_pipeline(sources=args.sources, output_dir=args.output_dir))


if __name__ == "__main__":
    main()

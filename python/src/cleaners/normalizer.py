"""数据清洗与标准化"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from python.src.models.raw_intelligence import RawIntelligence

logger = logging.getLogger(__name__)


def deduplicate(items: list[RawIntelligence]) -> list[RawIntelligence]:
    """基于 URL 去重"""
    seen: set[str] = set()
    unique: list[RawIntelligence] = []
    for item in items:
        if item.url not in seen:
            seen.add(item.url)
            unique.append(item)
    removed = len(items) - len(unique)
    if removed > 0:
        logger.info(f"去重: 移除 {removed} 条重复情报")
    return unique


def sort_by_time(items: list[RawIntelligence]) -> list[RawIntelligence]:
    """按发布时间降序排列（最新在前）"""
    return sorted(items, key=lambda x: x.published_at, reverse=True)


def truncate_content(items: list[RawIntelligence], max_length: int = 5000) -> list[RawIntelligence]:
    """截断过长的 rawContent，节省 Agent token"""
    for item in items:
        if len(item.raw_content) > max_length:
            item.raw_content = item.raw_content[:max_length] + "..."
    return items


def normalize(items: list[RawIntelligence]) -> list[RawIntelligence]:
    """完整的清洗管道"""
    items = deduplicate(items)
    items = truncate_content(items)
    items = sort_by_time(items)
    logger.info(f"清洗完成: {len(items)} 条有效情报")
    return items


def content_hash(item: RawIntelligence) -> str:
    """生成内容指纹，用于更精确的去重"""
    raw = f"{item.source.value}:{item.title}:{item.url}"
    return hashlib.md5(raw.encode()).hexdigest()

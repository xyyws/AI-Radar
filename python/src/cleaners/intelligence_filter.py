"""情报智能过滤 — 各源用自己的指标评分，不归一化"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher

from python.src.models.raw_intelligence import RawIntelligence, Source

logger = logging.getLogger(__name__)

# 大厂官方源的基础权重（无互动数据时使用）
BLOG_SOURCE_WEIGHT: dict[Source, float] = {
    Source.ARXIV: 8.0,
    Source.OPENAI: 9.0,
    Source.ANTHROPIC: 9.0,
    Source.DEEPMIND: 9.0,
    Source.META: 8.0,
    Source.WECHAT: 6.0,
    Source.ZHIHU: 5.0,
}


def _time_decay(published_at: datetime, half_life_hours: float = 12.0) -> float:
    """时间衰减因子，half_life_hours 小时内衰减到 0.5"""
    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    hours_ago = max(0, (now - published_at).total_seconds() / 3600)
    return math.exp(-0.693 * hours_ago / half_life_hours)


def _score_github(item: RawIntelligence) -> float:
    """GitHub: stars + 时间衰减"""
    meta = item.metadata or {}
    stars_str = str(meta.get("today_stars", "0"))
    # 从 "1,234 stars today" 中提取数字
    stars = 0
    for word in stars_str.replace(",", "").split():
        if word.isdigit():
            stars = int(word)
            break

    # stars 贡献：对数缩放，100 stars ≈ 5分
    star_score = min(10, math.log10(max(1, stars)) * 2.5)

    # 时间衰减
    decay = _time_decay(item.published_at)

    return star_score * decay + 2  # 基础分 2


def _score_huggingface(item: RawIntelligence) -> float:
    """HuggingFace: downloads + likes + 时间衰减"""
    meta = item.metadata or {}
    downloads = meta.get("downloads", 0) or 0
    likes = meta.get("likes", 0) or 0

    # downloads 对数缩放：1M ≈ 7分
    dl_score = min(7, math.log10(max(1, downloads)) * 1.0) if downloads else 0

    # likes 线性：100 likes ≈ 3分
    like_score = min(3, likes / 33) if likes else 0

    decay = _time_decay(item.published_at)

    return (dl_score + like_score) * decay + 2


def _score_reddit(item: RawIntelligence) -> float:
    """Reddit: score(点赞净数) + comments + 时间衰减"""
    meta = item.metadata or {}
    score = meta.get("score", 0) or 0
    comments = meta.get("comments", 0) or 0

    # score 对数缩放：500 score ≈ 6分
    score_pts = min(6, math.log10(max(1, score)) * 1.8) if score else 0

    # comments：50 comments ≈ 4分
    comment_pts = min(4, math.log10(max(1, comments)) * 1.5) if comments else 0

    decay = _time_decay(item.published_at, half_life_hours=8)  # Reddit 热度衰减更快

    return (score_pts + comment_pts) * decay + 1


def _score_twitter(item: RawIntelligence) -> float:
    """Twitter/X: retweets + likes + 时间衰减"""
    meta = item.metadata or {}
    retweets = meta.get("retweets", 0) or 0
    likes = meta.get("likes", 0) or 0

    rt_score = min(5, math.log10(max(1, retweets)) * 1.5) if retweets else 0
    like_score = min(5, math.log10(max(1, likes)) * 1.2) if likes else 0

    decay = _time_decay(item.published_at, half_life_hours=6)  # Twitter 衰减最快

    return (rt_score + like_score) * decay + 1


def _score_blog(item: RawIntelligence) -> float:
    """大厂 Blog / Arxiv / 微信 / 知乎：无互动数据，用基础权重 + 时间衰减"""
    base = BLOG_SOURCE_WEIGHT.get(item.source, 5.0)
    decay = _time_decay(item.published_at, half_life_hours=24)  # Blog 衰减慢
    return base * decay


def compute_score(item: RawIntelligence) -> float:
    """根据数据源类型选择对应的评分策略"""
    scorers = {
        Source.GITHUB: _score_github,
        Source.HUGGINGFACE: _score_huggingface,
        Source.REDDIT: _score_reddit,
        Source.TWITTER: _score_twitter,
    }

    scorer = scorers.get(item.source, _score_blog)
    return scorer(item)


def deduplicate_by_similarity(
    items: list[RawIntelligence], threshold: float = 0.6
) -> list[RawIntelligence]:
    """基于标题相似度去重"""
    if len(items) <= 1:
        return items

    unique: list[RawIntelligence] = [items[0]]
    for item in items[1:]:
        is_dup = False
        for existing in unique:
            title_sim = SequenceMatcher(
                None, item.title.lower(), existing.title.lower()
            ).ratio()
            if item.source == existing.source and title_sim > threshold:
                is_dup = True
                break
            if title_sim > 0.8:
                if compute_score(item) > compute_score(existing):
                    unique.remove(existing)
                else:
                    is_dup = True
                break

        if not is_dup:
            unique.append(item)

    removed = len(items) - len(unique)
    if removed > 0:
        logger.info(f"相似度去重: 移除 {removed} 条")
    return unique


def diversify_sources(items: list[RawIntelligence], max_per_source: int = 8) -> list[RawIntelligence]:
    """确保来源多样性"""
    source_count: dict[Source, int] = defaultdict(int)
    diversified: list[RawIntelligence] = []
    for item in items:
        if source_count[item.source] < max_per_source:
            diversified.append(item)
            source_count[item.source] += 1
    return diversified


def select_top_intelligence(
    items: list[RawIntelligence], max_items: int = 30
) -> list[RawIntelligence]:
    """精选高质量情报"""
    logger.info(f"开始智能过滤，原始 {len(items)} 条")

    items = deduplicate_by_similarity(items)

    scored = [(compute_score(item), item) for item in items]
    scored.sort(key=lambda x: x[0], reverse=True)

    # 打印 top 5 供调试
    for s, item in scored[:5]:
        logger.info(f"  [{item.source.value}] {s:.1f}分 {item.title[:50]}")

    sorted_items = [item for _, item in scored]
    sorted_items = diversify_sources(sorted_items)
    selected = sorted_items[:max_items]

    logger.info(f"智能过滤完成: {len(selected)} 条精选情报")
    return selected

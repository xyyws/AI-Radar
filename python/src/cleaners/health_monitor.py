"""采集健康监控 — 每日记录指标，异常时报警"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from python.src.models.raw_intelligence import RawIntelligence, Source

logger = logging.getLogger(__name__)

HEALTH_FILE = Path("data/health.json")


def _field_completeness(items: list[RawIntelligence]) -> float:
    """字段完整率：标题、URL、发布时间、原始内容全部非空的比例"""
    if not items:
        return 0.0

    complete = 0
    for item in items:
        if (item.title and item.title.strip()
            and item.url and item.url.strip()
            and item.raw_content and item.raw_content.strip()):
            complete += 1

    return round(complete / len(items) * 100, 1)


def _source_breakdown(items: list[RawIntelligence]) -> dict[str, int]:
    """按源统计条数"""
    breakdown: dict[str, int] = {}
    for item in items:
        key = item.source.value
        breakdown[key] = breakdown.get(key, 0) + 1
    return breakdown


def _load_history(health_file: Path) -> list[dict]:
    """加载历史指标"""
    if not health_file.exists():
        return []
    try:
        return json.loads(health_file.read_text(encoding="utf-8"))
    except Exception:
        return []


def _detect_anomalies(
    today: dict,
    history: list[dict],
) -> list[str]:
    """对比历史基线，检测异常"""
    alerts: list[str] = []

    if len(history) < 3:
        alerts.append("历史数据不足 3 天，跳过基线对比")
        return alerts

    # 1. 全量条数对比
    recent_totals = [h.get("total_items", 0) for h in history[-7:]]
    avg_total = sum(recent_totals) / len(recent_totals)
    today_total = today.get("total_items", 0)

    if avg_total > 0:
        change_pct = (today_total - avg_total) / avg_total * 100
        if change_pct < -50:
            alerts.append(f"⚠️ 全量腰斩: {today_total} 条 (7日均值 {avg_total:.0f} 条, 变化 {change_pct:.0f}%)")
        elif change_pct < -30:
            alerts.append(f"⚡ 全量下降: {today_total} 条 (7日均值 {avg_total:.0f} 条, 变化 {change_pct:.0f}%)")

    # 2. 单源对比
    for source, count in today.get("source_breakdown", {}).items():
        source_history = [
            h.get("source_breakdown", {}).get(source, 0)
            for h in history[-7:]
        ]
        if not source_history:
            continue

        avg_source = sum(source_history) / len(source_history)
        if avg_source > 0:
            change = (count - avg_source) / avg_source * 100
            if count == 0 and avg_source > 5:
                alerts.append(f"🔴 {source} 挂了: 0 条 (7日均值 {avg_source:.0f} 条)")
            elif change < -70:
                alerts.append(f"🟠 {source} 异常下降: {count} 条 (7日均值 {avg_source:.0f} 条, {change:.0f}%)")

    # 3. 字段完整率
    completeness = today.get("field_completeness", 100)
    if completeness < 80:
        alerts.append(f"⚠️ 字段完整率低: {completeness}% (阈值 80%)")

    # 4. 去重率
    dedup_rate = today.get("dedup_rate", 0)
    if dedup_rate > 70:
        alerts.append(f"⚠️ 去重率异常高: {dedup_rate}% — 可能卡在同一页反复抓取")

    return alerts


def record_health(
    items: list[RawIntelligence],
    raw_count: int,
    dedup_removed: int,
    health_file: Path = HEALTH_FILE,
) -> dict:
    """记录今日采集健康指标"""

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    breakdown = _source_breakdown(items)
    completeness = _field_completeness(items)
    dedup_rate = round(dedup_removed / raw_count * 100, 1) if raw_count > 0 else 0

    record = {
        "date": today,
        "total_items": len(items),
        "raw_count": raw_count,
        "dedup_removed": dedup_removed,
        "dedup_rate": dedup_rate,
        "field_completeness": completeness,
        "source_breakdown": breakdown,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    # 加载历史 & 检测异常
    history = _load_history(health_file)
    alerts = _detect_anomalies(record, history)
    record["alerts"] = alerts

    # 追加今日记录（保留最近 30 天）
    history.append(record)
    history = history[-30:]

    health_file.parent.mkdir(parents=True, exist_ok=True)
    health_file.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 输出日志
    logger.info(f"健康指标: {len(items)}条 | 完整率{completeness}% | 去重率{dedup_rate}%")
    for alert in alerts:
        logger.warning(f"  {alert}")

    return record

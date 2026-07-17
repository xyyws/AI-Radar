"""DailyAIRadarReport 数据模型 — 与 shared/schema/daily-report.json 对齐"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class RadarEvent(BaseModel):
    """单个核心事件"""

    title: str = Field(min_length=1, max_length=200, description="事件标题")
    what: str = Field(
        min_length=10, max_length=1000,
        description="是什么 — 事件/技术/产品的本质描述",
    )
    why_important: str = Field(
        min_length=10, max_length=1000,
        description="为什么重要 — 技术范式转变或产业颠覆性分析",
        alias="whyImportant",
    )
    adoption: str = Field(
        min_length=5, max_length=1000,
        description="哪些公司开始用了 — 商业采纳情况，无线索时标注'研判'",
    )
    trend: str = Field(
        min_length=10, max_length=1000,
        description="未来趋势 — 短期和中期发展预判",
    )
    tags: list[str] = Field(min_length=1, max_length=10, description="事件标签")

    model_config = {"populate_by_name": True}


class DailyAIRadarReport(BaseModel):
    """Agent 提炼后的每日 AI 情报报告"""

    date: date = Field(description="报告日期，YYYY-MM-DD 格式")
    summary: str = Field(
        min_length=100, max_length=2000,
        description="500 字左右的每日总览",
    )
    events: list[RadarEvent] = Field(
        min_length=1, max_length=10,
        description="核心事件列表，通常 3-5 个",
    )
    keywords: list[str] = Field(
        min_length=1, max_length=20,
        description="关键词 / 新名词列表",
    )

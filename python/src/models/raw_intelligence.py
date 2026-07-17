"""RawIntelligence 数据模型 — 与 shared/schema/raw-intelligence.json 对齐"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Source(str, Enum):
    GITHUB = "github"
    ARXIV = "arxiv"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPMIND = "deepmind"
    META = "meta"
    HUGGINGFACE = "huggingface"
    TWITTER = "twitter"
    REDDIT = "reddit"
    WECHAT = "wechat"
    ZHIHU = "zhihu"


class Language(str, Enum):
    EN = "en"
    ZH = "zh"


class RawIntelligence(BaseModel):
    """统一的原始情报数据格式，所有 11 个数据源的输出都必须符合此模型"""

    source: Source = Field(description="数据源标识")
    title: str = Field(min_length=1, max_length=500, description="情报标题")
    url: str = Field(description="原始链接")
    raw_content: str = Field(
        min_length=1,
        max_length=10000,
        description="原始内容（标题 + 摘要 / 正文片段）",
        alias="rawContent",
    )
    published_at: datetime = Field(
        description="发布时间，ISO 8601 格式",
        alias="publishedAt",
    )
    language: Language = Field(description="内容语言")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="源特有字段",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="证据列表：关键数据点、引用、指标等",
    )

    model_config = {"populate_by_name": True}

"""Схемы встроенной справки."""

from pydantic import BaseModel, Field


class HelpTopicRef(BaseModel):
    slug: str
    title: str
    summary: str


class HelpTopicOut(HelpTopicRef):
    body: str = Field(description="Текст раздела в Markdown")

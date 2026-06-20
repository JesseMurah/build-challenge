from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import BigInteger, Column, JSON
from sqlmodel import Field, SQLModel


class Modality(str, enum.Enum):
    text = "text"
    voice = "voice"
    document = "document"


class Category(str, enum.Enum):
    request = "request"
    issue = "issue"
    decision = "decision"
    update = "update"
    question = "question"
    noise = "noise"


class Priority(str, enum.Enum):
    now = "now"
    today = "today"
    whenever = "whenever"


class Entry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    team_id: int = Field(sa_column=Column(BigInteger, index=True))
    sender_id: int = Field(sa_column=Column(BigInteger))
    sender_name: str
    modality: Modality
    category: Category
    priority: Priority
    content: str
    raw: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.models import Category, Entry, Priority


@dataclass
class TelegramUpdate:
    """Minimal representation of an inbound Telegram group event."""
    team_id: int
    sender_id: int
    sender_name: str
    text: str | None
    voice_bytes: bytes | None
    document_bytes: bytes | None
    raw: dict


class AIProvider(Protocol):
    def classify(self, content: str) -> tuple[Category, Priority]: ...
    def transcribe(self, audio: bytes) -> str: ...
    def extract(self, document: bytes) -> str: ...
    def summarize(self, entries: list[Entry], draft: str) -> str: ...


class EntryRepository(Protocol):
    def save(self, entry: Entry) -> Entry: ...
    def find_by_team(self, team_id: int, since: datetime) -> list[Entry]: ...

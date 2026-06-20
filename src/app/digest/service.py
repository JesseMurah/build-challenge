from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session

from app.domain.models import Category, Entry, Priority
from app.domain.ports import AIProvider
from app.infrastructure.repository import SqlEntryRepository

_PRIORITY_ORDER = {Priority.now: 0, Priority.today: 1, Priority.whenever: 2}
_QUIET_DAY = "No operational entries recorded in this period. Quiet day."


def build_digest(
    team_id: int,
    window: timedelta,
    session: Session,
    provider: AIProvider,
) -> str:
    since = datetime.now(timezone.utc) - window
    repo = SqlEntryRepository(session)
    entries = repo.find_by_team(team_id=team_id, since=since)

    if not entries:
        return _QUIET_DAY

    draft = _format_draft(entries)
    return provider.summarize(entries, draft)


def _format_draft(entries: list[Entry]) -> str:
    by_category: dict[Category, list[Entry]] = {}
    for entry in entries:
        by_category.setdefault(entry.category, []).append(entry)

    sections: list[str] = []
    for category in Category:
        if category is Category.noise or category not in by_category:
            continue
        group = sorted(by_category[category], key=lambda e: _PRIORITY_ORDER[e.priority])
        lines = [f"## {category.value.upper()}"]
        for e in group:
            tag = f"[{e.priority.value}]"
            lines.append(f"- {tag} {e.content} — {e.sender_name}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)

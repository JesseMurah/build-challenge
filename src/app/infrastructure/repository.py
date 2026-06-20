from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.domain.models import Entry


class SqlEntryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, entry: Entry) -> Entry:
        self._session.add(entry)
        self._session.commit()
        self._session.refresh(entry)
        return entry

    def find_by_team(self, team_id: int, since: datetime) -> list[Entry]:
        stmt = (
            select(Entry)
            .where(Entry.team_id == team_id)
            .where(Entry.created_at >= since)
        )
        return list(self._session.exec(stmt).all())

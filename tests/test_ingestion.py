from datetime import datetime, timedelta, timezone

import pytest

from app.domain.models import Category, Modality, Priority
from app.domain.ports import TelegramUpdate
from app.ingestion.service import ingest


def make_text_update(team_id=1, sender_id=42, sender_name="Alice", text="We are blocked on the API"):
    return TelegramUpdate(
        team_id=team_id,
        sender_id=sender_id,
        sender_name=sender_name,
        text=text,
        voice_bytes=None,
        document_bytes=None,
        raw={"message_id": 99},
    )


# --- Behavior 1: text Update → persisted Entry ---

def test_text_update_produces_entry(fake_provider, db_session):
    update = make_text_update()

    entry = ingest(update, fake_provider, db_session)

    assert entry is not None
    assert entry.id is not None
    assert entry.team_id == 1
    assert entry.sender_id == 42
    assert entry.sender_name == "Alice"
    assert entry.modality == Modality.text
    assert entry.content == "We are blocked on the API"
    assert entry.category == Category.request
    assert entry.priority == Priority.today


# --- Behavior 2: noise gate ---

def test_noise_update_is_discarded(noise_provider, db_session):
    update = make_text_update(text="lol 👍")

    entry = ingest(update, noise_provider, db_session)

    assert entry is None


# --- Behavior 3 & 4: EntryRepository window + team isolation ---

def test_find_by_team_respects_time_window(fake_provider, db_session):
    from app.infrastructure.repository import SqlEntryRepository

    repo = SqlEntryRepository(db_session)
    recent_update = make_text_update(team_id=1)
    ingest(recent_update, fake_provider, db_session)

    since = datetime.now(tz=timezone.utc) - timedelta(hours=25)
    entries = repo.find_by_team(team_id=1, since=since)
    assert len(entries) == 1


def test_find_by_team_isolates_teams(fake_provider, db_session):
    from app.infrastructure.repository import SqlEntryRepository

    repo = SqlEntryRepository(db_session)
    ingest(make_text_update(team_id=1), fake_provider, db_session)
    ingest(make_text_update(team_id=2), fake_provider, db_session)

    since = datetime.now(tz=timezone.utc) - timedelta(hours=25)
    entries = repo.find_by_team(team_id=1, since=since)
    assert len(entries) == 1
    assert all(e.team_id == 1 for e in entries)

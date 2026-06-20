import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.models import Category, Modality, Priority
from app.scheduler import digest_job, schedule_daily_digest


def make_context(session, provider, sent_messages: list) -> MagicMock:
    """Build a fake PTB ContextTypes.DEFAULT_TYPE."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        side_effect=lambda chat_id, text: sent_messages.append((chat_id, text))
    )
    ctx = MagicMock()
    ctx.bot = bot
    ctx.bot_data = {"session": session, "provider": provider}
    return ctx


# --- Behavior 1: schedule_daily_digest registers one global job ---

def test_schedule_registers_one_daily_job():
    app = MagicMock()
    digest_time = datetime.time(8, 0, tzinfo=datetime.timezone.utc)

    schedule_daily_digest(app, digest_time)

    app.job_queue.run_daily.assert_called_once_with(digest_job, digest_time)


# --- Behavior 2: digest_job sends the digest to each active team ---

@pytest.mark.asyncio
async def test_digest_job_sends_to_each_active_team(fake_provider, db_session):
    from sqlmodel import Session
    from app.domain.models import Entry

    # Seed entries for two teams
    for team_id in [101, 202]:
        db_session.add(Entry(
            team_id=team_id, sender_id=1, sender_name="Alice",
            modality=Modality.text, category=Category.update,
            priority=Priority.today, content=f"team {team_id} news",
        ))
    db_session.commit()

    sent: list = []
    ctx = make_context(db_session, fake_provider, sent)

    await digest_job(ctx)

    team_ids_notified = {chat_id for chat_id, _ in sent}
    assert 101 in team_ids_notified
    assert 202 in team_ids_notified


# --- Behavior 3: digest_job sends quiet-day message when no entries ---

@pytest.mark.asyncio
async def test_digest_job_skips_teams_with_no_entries(fake_provider, db_session):
    """No entries → no teams → no messages sent."""
    sent: list = []
    ctx = make_context(db_session, fake_provider, sent)

    await digest_job(ctx)

    assert sent == []

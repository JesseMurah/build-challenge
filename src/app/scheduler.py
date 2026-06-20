from __future__ import annotations

import datetime
import logging
from datetime import timedelta

from sqlmodel import Session, select

from app.digest.service import build_digest
from app.domain.models import Entry

logger = logging.getLogger(__name__)

_DIGEST_WINDOW = timedelta(hours=24)


def get_active_team_ids(session: Session) -> list[int]:
    rows = session.exec(select(Entry.team_id).distinct()).all()
    return list(rows)


async def digest_job(context) -> None:
    session: Session = context.bot_data["session"]
    provider = context.bot_data["provider"]

    team_ids = get_active_team_ids(session)
    for team_id in team_ids:
        try:
            text = build_digest(team_id, _DIGEST_WINDOW, session, provider)
            await context.bot.send_message(chat_id=team_id, text=text)
        except Exception:
            logger.exception("digest_job failed for team=%s", team_id)


def schedule_daily_digest(application, digest_time: datetime.time) -> None:
    application.job_queue.run_daily(digest_job, digest_time)

from __future__ import annotations

from sqlmodel import Session

from app.domain.models import Category, Entry, Modality
from app.domain.ports import AIProvider, TelegramUpdate


def ingest(update: TelegramUpdate, provider: AIProvider, session: Session) -> Entry | None:
    if update.voice_bytes is not None:
        modality = Modality.voice
        content = provider.transcribe(update.voice_bytes)
    elif update.document_bytes is not None:
        modality = Modality.document
        content = provider.extract(update.document_bytes)
    else:
        modality = Modality.text
        content = update.text or ""

    category, priority = provider.classify(content)

    if category is Category.noise:
        return None

    entry = Entry(
        team_id=update.team_id,
        sender_id=update.sender_id,
        sender_name=update.sender_name,
        modality=modality,
        category=category,
        priority=priority,
        content=content,
        raw=update.raw,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

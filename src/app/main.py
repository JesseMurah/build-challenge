from __future__ import annotations

import datetime
import io
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from sqlmodel import Session, SQLModel, create_engine
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import get_gemini_provider, get_settings
from app.domain.models import Entry  # noqa: F401 — registers table with SQLModel metadata
from app.domain.ports import TelegramUpdate
from app.ingestion.service import ingest_safe
from app.digest.service import build_digest
from app.scheduler import schedule_daily_digest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
engine = create_engine(settings.database_url, echo=False)


# ---------------------------------------------------------------------------
# PTB handlers
# ---------------------------------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.from_user:
        return
    tg = TelegramUpdate(
        team_id=msg.chat.id,
        sender_id=msg.from_user.id,
        sender_name=msg.from_user.full_name,
        text=msg.text,
        voice_bytes=None,
        document_bytes=None,
        raw={"message_id": msg.message_id},
    )
    with Session(engine) as session:
        ingest_safe(tg, context.bot_data["provider"], session)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.from_user or not msg.voice:
        return
    tg_file = await context.bot.get_file(msg.voice.file_id)
    buf = io.BytesIO()
    await tg_file.download_to_memory(buf)
    buf.seek(0)
    tg = TelegramUpdate(
        team_id=msg.chat.id,
        sender_id=msg.from_user.id,
        sender_name=msg.from_user.full_name,
        text=None,
        voice_bytes=buf.read(),
        document_bytes=None,
        raw={"message_id": msg.message_id},
    )
    with Session(engine) as session:
        ingest_safe(tg, context.bot_data["provider"], session)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.from_user or not msg.document:
        return
    tg_file = await context.bot.get_file(msg.document.file_id)
    buf = io.BytesIO()
    await tg_file.download_to_memory(buf)
    buf.seek(0)
    tg = TelegramUpdate(
        team_id=msg.chat.id,
        sender_id=msg.from_user.id,
        sender_name=msg.from_user.full_name,
        text=None,
        voice_bytes=None,
        document_bytes=buf.read(),
        raw={"message_id": msg.message_id, "file_name": msg.document.file_name},
    )
    with Session(engine) as session:
        ingest_safe(tg, context.bot_data["provider"], session)


async def handle_digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """On-demand /digest — demo trigger."""
    msg = update.message
    if not msg:
        return
    from datetime import timedelta
    with Session(engine) as session:
        text = build_digest(
            team_id=msg.chat.id,
            window=timedelta(hours=24),
            session=session,
            provider=context.bot_data["provider"],
        )
    await msg.reply_text(text)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables ready")

    # Build PTB application
    ptb_app: Application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # Wire shared resources into bot_data
    ptb_app.bot_data["provider"] = get_gemini_provider()

    # Register handlers (group chats only + DMs for /digest)
    group_filter = filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP
    ptb_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND & group_filter, handle_text)
    )
    ptb_app.add_handler(MessageHandler(filters.VOICE & group_filter, handle_voice))
    ptb_app.add_handler(MessageHandler(filters.Document.ALL & group_filter, handle_document))
    ptb_app.add_handler(CommandHandler("digest", handle_digest_command))

    # Start PTB (initialises JobQueue etc.)
    await ptb_app.initialize()
    await ptb_app.start()

    # Register webhook with Telegram
    webhook_url = f"{settings.webhook_url}/webhook"
    await ptb_app.bot.set_webhook(url=webhook_url)
    logger.info("Webhook registered: %s", webhook_url)

    # Schedule daily digest
    digest_time = datetime.time(settings.digest_hour, 0, tzinfo=datetime.timezone.utc)
    schedule_daily_digest(ptb_app, digest_time)
    logger.info("Daily digest scheduled at %02d:00 UTC", settings.digest_hour)

    app.state.ptb = ptb_app
    yield

    # Shutdown
    await ptb_app.bot.delete_webhook()
    await ptb_app.stop()
    await ptb_app.shutdown()
    logger.info("Shutdown complete")


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    data = await request.json()
    update = Update.de_json(data, request.app.state.ptb.bot)
    await request.app.state.ptb.process_update(update)
    return Response(status_code=200)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

from unittest.mock import MagicMock

from app.domain.models import Category, Priority
from app.domain.ports import TelegramUpdate
from app.ingestion.service import ingest_safe


def make_update(text: str = "We need help", team_id: int = 1) -> TelegramUpdate:
    return TelegramUpdate(
        team_id=team_id, sender_id=1, sender_name="Alice",
        text=text, voice_bytes=None, document_bytes=None,
        raw={},
    )


def exploding_provider(exception: Exception):
    """AIProvider whose classify() raises."""
    provider = MagicMock()
    provider.classify.side_effect = exception
    provider.transcribe.return_value = "transcribed"
    provider.extract.return_value = "extracted"
    return provider


# --- Behavior 1: classify failure → None, no raise ---

def test_classify_exception_returns_none(db_session):
    provider = exploding_provider(RuntimeError("Gemini is down"))
    result = ingest_safe(make_update(), provider, db_session)
    assert result is None  # no raise, no entry


# --- Behavior 2: transcribe failure → None, no raise ---

def test_transcribe_exception_returns_none(db_session):
    provider = MagicMock()
    provider.transcribe.side_effect = ConnectionError("network timeout")
    update = TelegramUpdate(
        team_id=1, sender_id=1, sender_name="Alice",
        text=None, voice_bytes=b"ogg", document_bytes=None, raw={},
    )
    result = ingest_safe(update, provider, db_session)
    assert result is None


# --- Behavior 3: pipeline continues after a failing update ---

def test_second_update_succeeds_after_first_fails(fake_provider, db_session):
    bad_provider = exploding_provider(RuntimeError("timeout"))
    ingest_safe(make_update(text="this will fail"), bad_provider, db_session)

    # Now a valid update with the working fake_provider
    result = ingest_safe(make_update(text="this should work"), fake_provider, db_session)
    assert result is not None
    assert result.content == "this should work"


# --- Behavior 4: ingest_safe never raises, even on unexpected errors ---

def test_ingest_safe_never_raises(db_session):
    provider = exploding_provider(Exception("completely unexpected"))
    try:
        ingest_safe(make_update(), provider, db_session)
    except Exception as exc:
        raise AssertionError(f"ingest_safe raised unexpectedly: {exc}") from exc

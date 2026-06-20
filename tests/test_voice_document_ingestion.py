from app.domain.models import Category, Modality, Priority
from app.domain.ports import TelegramUpdate
from app.ingestion.service import ingest


def make_voice_update(audio: bytes = b"fake-ogg") -> TelegramUpdate:
    return TelegramUpdate(
        team_id=1, sender_id=42, sender_name="Alice",
        text=None, voice_bytes=audio, document_bytes=None,
        raw={},
    )


def make_document_update(data: bytes = b"fake-pdf") -> TelegramUpdate:
    return TelegramUpdate(
        team_id=1, sender_id=42, sender_name="Alice",
        text=None, voice_bytes=None, document_bytes=data,
        raw={},
    )


# --- Voice: transcript becomes Content, Modality=voice ---

def test_voice_update_transcribes_to_content(fake_provider, db_session):
    update = make_voice_update()
    entry = ingest(update, fake_provider, db_session)

    assert entry is not None
    assert entry.modality == Modality.voice
    assert entry.content == "transcribed text"   # FakeAIProvider.transcribe returns this


def test_voice_entry_is_classified_and_attributed(fake_provider, db_session):
    update = make_voice_update()
    entry = ingest(update, fake_provider, db_session)

    assert entry.category == Category.request    # FakeAIProvider default
    assert entry.priority == Priority.today
    assert entry.sender_name == "Alice"
    assert entry.team_id == 1


# --- Document: extracted text becomes Content, Modality=document ---

def test_document_update_extracts_to_content(fake_provider, db_session):
    update = make_document_update()
    entry = ingest(update, fake_provider, db_session)

    assert entry is not None
    assert entry.modality == Modality.document
    assert entry.content == "extracted text"     # FakeAIProvider.extract returns this


def test_document_entry_is_classified_and_attributed(fake_provider, db_session):
    update = make_document_update()
    entry = ingest(update, fake_provider, db_session)

    assert entry.category == Category.request
    assert entry.priority == Priority.today
    assert entry.sender_name == "Alice"


# --- Priority between modalities: voice beats text, document beats text ---

def test_voice_takes_priority_over_text_field(fake_provider, db_session):
    """If voice_bytes is set, text is ignored and voice path is used."""
    update = TelegramUpdate(
        team_id=1, sender_id=1, sender_name="Bob",
        text="ignore this text",
        voice_bytes=b"ogg-data",
        document_bytes=None,
        raw={},
    )
    entry = ingest(update, fake_provider, db_session)
    assert entry.modality == Modality.voice
    assert entry.content == "transcribed text"

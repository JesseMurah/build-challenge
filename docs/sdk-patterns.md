# SDK Patterns

Verified against live docs. Update this file when docs change — never code from memory.

## Gemini (google-genai)

Docs: https://ai.google.dev/gemini-api/docs

```bash
pip install google-genai          # NOT google-generativeai (different package)
```

```python
from google import genai
from google.genai import types

client = genai.Client()                        # reads GEMINI_API_KEY from env
client = genai.Client(api_key="your-key")     # or pass explicitly (preferred in factory)
```

### Audio transcription

OGG Vorbis is natively supported — Telegram voice notes are OGG Vorbis, no conversion needed.

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        "Transcribe this audio exactly.",
        types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
    ],
)
transcript = response.text
```

Supported formats: WAV, MP3, AIFF, AAC, OGG Vorbis, FLAC.

### Document extraction

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        "Extract the full text content.",
    ],
)
text = response.text
```

### Structured output (classification)

Use Pydantic `Literal` types + `response_format` to constrain output to exact enum values.
Parse with `model_validate_json` — no manual parsing.

```python
from pydantic import BaseModel
from typing import Literal

class Classification(BaseModel):
    category: Literal["request", "issue", "decision", "update", "question", "noise"]
    priority: Literal["now", "today", "whenever"]

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=content_text,
    config={
        "response_format": {
            "text": {
                "mime_type": "application/json",
                "schema": Classification.model_json_schema(),
            }
        }
    },
)
result = Classification.model_validate_json(response.text)
# result.category and result.priority are guaranteed valid literals
```

---

## python-telegram-bot (PTB)

Docs: https://python-telegram-bot.org/ · https://core.telegram.org/bots/api

```bash
pip install python-telegram-bot --upgrade   # current: v22.8, Python 3.10+, fully async
```

```python
from telegram import Bot, Update, Voice, Document, File
from telegram.ext import Application, ApplicationBuilder, MessageHandler, ContextTypes, filters
```

### Message fields

```python
update.message.chat.id              # int — team_id (the group chat)
update.message.from_user            # User | None — None for channel posts, always guard
update.message.from_user.id         # int — sender_id
update.message.from_user.full_name  # str — sender display name
update.message.text                 # str | None
update.message.voice                # Voice | None
update.message.document             # Document | None
```

### Voice type

```python
message.voice.file_id       # str
message.voice.duration      # int (seconds)
message.voice.mime_type     # str | None (typically "audio/ogg")
message.voice.file_size     # int | None
```

### Document type

```python
message.document.file_id    # str
message.document.file_name  # str | None
message.document.mime_type  # str | None
message.document.file_size  # int | None
```

### Downloading files

`download_to_memory` writes into a caller-provided `BytesIO` (returns None, not the buffer):

```python
import io
tg_file = await context.bot.get_file(message.voice.file_id)
buf = io.BytesIO()
await tg_file.download_to_memory(buf)
buf.seek(0)
audio_bytes: bytes = buf.read()
```

### FastAPI webhook wiring

Use `Application`, not `Updater`. Parse with `de_json`, not `model_validate`:

```python
from telegram import Update

@app.post("/webhook")
async def webhook(request: Request) -> None:
    update = Update.de_json(await request.json(), bot)
    await application.process_update(update)
```

### Application setup

```python
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT, handle_message))
application.add_handler(MessageHandler(filters.VOICE, handle_voice))
application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
```

### JobQueue — scheduling daily tasks

JobQueue starts automatically with `run_polling()` / `run_webhook()` — no manual start.

```python
import datetime

# Register a daily job at a fixed clock time
application.job_queue.run_daily(
    callback,
    time=datetime.time(8, 0, tzinfo=datetime.timezone.utc),  # 08:00 UTC daily
    chat_id=team_id,           # accessible as context.job.chat_id inside callback
    data={"team_id": team_id}, # any object — accessible as context.job.data
)

# Callback signature — no update arg
async def digest_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=context.job.chat_id, text="digest text")
```

Pass shared resources (DB session, provider) via `application.bot_data`:

```python
application.bot_data["session"] = session
application.bot_data["provider"] = provider

# Inside callback:
session  = context.bot_data["session"]
provider = context.bot_data["provider"]
```

---

## FastAPI

Docs: https://fastapi.tiangolo.com/

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
```

Startup/shutdown lifecycle (wire bot and DB here):

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown

app = FastAPI(lifespan=lifespan)
```

# OpsPulse — AI-Powered Operational Intelligence for Teams

A Telegram bot that watches your team's group chat, classifies every message by type and urgency using Gemini AI, and delivers a daily operational digest — turning the noise of a busy group into a clear, prioritised summary with recommended next steps.

**Core loop: Information → Intelligence → Action**

---

## What It Does

Teams communicate in Telegram but lose track of what matters. OpsPulse silently captures every operational message — text, voice note, or document — classifies it, and rolls it up into a daily digest delivered to the group. No filing, no tagging, no extra tools.

| Input | What happens |
|---|---|
| Text message | Classified by type and urgency, stored |
| Voice note | Transcribed by Gemini, then classified and stored |
| Document (PDF, etc.) | Text extracted by Gemini, then classified and stored |
| `/digest` | On-demand digest delivered instantly (great for demos) |
| Daily at 08:00 UTC | Automatic digest delivered to every active team |

### Classification

Every message is classified on two axes:

**Category** — `issue` · `request` · `decision` · `update` · `question` · `noise`

**Priority** — `now` (urgent/blocking) · `today` · `whenever`

Noise is discarded. Everything else is stored and surfaced in the digest grouped by category, ordered by priority, and attributed to the sender.

---

## Architecture

```
Telegram group chat
        │
        ▼ (webhook)
  ┌─────────────┐
  │  FastAPI    │  /webhook  /health  /digest (command)
  └──────┬──────┘
         │
         ▼
  ┌─────────────────────────┐
  │  python-telegram-bot    │  Dispatcher · JobQueue (daily digest)
  └──────┬──────────────────┘
         │
         ▼
  ┌─────────────────────────┐
  │   Ingestion Service     │  ingest_safe() → ingest()
  │   - resolve Modality    │  text / voice (transcribe) / document (extract)
  │   - classify via Gemini │  Category + Priority
  │   - noise gate          │  noise → discard
  └──────┬──────────────────┘
         │
         ├──────────────────────────┐
         ▼                          ▼
  ┌─────────────┐          ┌────────────────┐
  │  PostgreSQL │          │  Gemini 2.5    │
  │  (Entries)  │          │  Flash API     │
  └──────┬──────┘          └────────────────┘
         │
         ▼
  ┌─────────────────────────┐
  │   Digest Service        │  build_digest()
  │   - group by Category   │  issue → request → decision → update → question
  │   - order by Priority   │  now → today → whenever
  │   - attribute to Sender │
  │   - summarize via Gemini│  + recommended Actions
  └─────────────────────────┘
```

### Stack

| Layer | Technology |
|---|---|
| Bot framework | python-telegram-bot v22 |
| HTTP layer | FastAPI + uvicorn |
| AI provider | Google Gemini 2.5 Flash |
| Persistence | PostgreSQL + SQLModel |
| Scheduler | PTB built-in JobQueue (APScheduler) |
| Config | pydantic-settings |

---

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL running locally or hosted
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- A public HTTPS URL for the webhook (ngrok for local dev)

### 1. Clone and install

```bash
git clone https://github.com/JesseMurah/build-challenge.git
cd build-challenge
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=postgresql://user:password@localhost:5432/your_db
WEBHOOK_URL=https://xxxx.ngrok-free.app
DIGEST_HOUR=8
```

> **Important:** `DATABASE_URL` must use `postgresql://` (not `postgres://`). The app normalises `postgres://` automatically but explicit is safer.

### 3. Create the database

```bash
createdb your_db
```

Tables are created automatically on first startup — no migration tool needed.

### 4. Disable bot privacy mode

By default Telegram bots only receive `/commands` in groups. To capture all messages:

1. Message [@BotFather](https://t.me/BotFather)
2. Send `/setprivacy`
3. Select your bot → **Disable**

### 5. Start ngrok (local dev)

```bash
ngrok http 8000
```

Copy the `https://xxxx.ngrok-free.app` URL into `WEBHOOK_URL` in `.env`.

### 6. Run

```bash
uvicorn app.main:app --reload
```

You should see:

```
INFO: Database tables ready
INFO: Webhook registered: https://xxxx.ngrok-free.app/webhook
INFO: Daily digest scheduled at 08:00 UTC
INFO: Application startup complete.
```

### 7. Add the bot to a group

In Telegram: open your group → Add member → search your bot username → Add.

---

## Usage

| Action | Result |
|---|---|
| Send any text in the group | Silently captured and classified |
| Send a voice note | Transcribed, classified, and stored |
| Share a document | Text extracted, classified, and stored |
| Send `/digest` | Instant digest of the last 24 hours |
| Every day at `DIGEST_HOUR` UTC | Automatic digest delivered to the group |

### Example digest

```
## ISSUE
- [now] The deployment pipeline is broken and blocking the whole team — KingMurah

## REQUEST
- [today] Can someone review the PR by EOD? — KingMurah

## DECISION
- [whenever] We're using Gemini for all AI classification — KingMurah

## Recommended actions
• Immediately fix the broken deployment pipeline — it's blocking the team.
• Assign a reviewer for KingMurah's PR before end of day.
```

---

## Project Structure

```
src/app/
├── main.py                  # FastAPI app, PTB handlers, lifespan wiring
├── config.py                # pydantic-settings, get_gemini_provider() factory
├── scheduler.py             # daily digest job
├── domain/
│   ├── models.py            # Entry, Category, Priority, Modality (SQLModel)
│   └── ports.py             # AIProvider protocol, TelegramUpdate, EntryRepository
├── ingestion/
│   └── service.py           # ingest(), ingest_safe()
├── digest/
│   └── service.py           # build_digest()
└── infrastructure/
    ├── gemini_provider.py   # GeminiProvider — classify, transcribe, extract, summarize
    └── repository.py        # SqlEntryRepository
```

---

## Running Tests

```bash
pytest tests/ -v
```

27 tests covering ingestion (text/voice/document), the noise gate, Digest assembly (grouping/ordering/attribution/time-window), pipeline resilience, and the scheduler. The Gemini integration test is skipped unless `GEMINI_API_KEY` is set.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | From [@BotFather](https://t.me/BotFather) |
| `GEMINI_API_KEY` | ✅ | From [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `DATABASE_URL` | ✅ | `postgresql://user:pass@host:5432/db` |
| `WEBHOOK_URL` | ✅ | Public HTTPS URL (no trailing slash) |
| `DIGEST_HOUR` | ❌ | UTC hour for daily digest (default: `8`) |

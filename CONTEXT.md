# Context

AI-powered Telegram bot for operational excellence (72-hour build challenge).
Core loop: **Information → Intelligence → Action** — receive/classify/store
inputs, generate insights, then trigger or recommend actions.

## Stack

- **FastAPI** — HTTP layer (webhook endpoint for Telegram updates, health checks,
  any internal APIs).
- **aiogram** — Telegram bot framework; handlers, routers, FSM for multi-step
  conversations. The bot is the primary user interface.
- **PostgreSQL + SQLModel** — persistence. SQLModel models are the source of
  truth for the schema; migrations live alongside.

## Glossary

_Add domain terms as they're resolved (via `/grill-with-docs`). Seed terms:_

- **Update** — an inbound Telegram event (message, document, voice note, command).
- **Insight** — AI-generated summary, recommendation, or observation derived from
  stored Updates.
- **Action** — a triggered or recommended operation that closes the loop.

> Use these exact terms in issue titles, hypotheses, and test names. If a concept
> isn't here yet, that's a signal to add it — don't drift to synonyms.

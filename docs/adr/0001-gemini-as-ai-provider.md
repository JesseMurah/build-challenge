---
status: accepted
---

# Gemini as the sole AI provider

Voice notes are a central, casual input: team members drop them into the group
chat and expect them captured with no extra steps. The Anthropic (Claude) API does
not accept audio input, so an all-Claude design would require a separate
speech-to-text step (Whisper or a hosted STT) before any reasoning. Gemini accepts
audio, text, and documents natively.

We chose **Gemini as the single AI provider** for transcription, document
extraction, classification (Category, Priority), and summarization (Insights,
Digest). In a 72-hour build the dominant cost is integration surface and the number
of failure modes, not the marginal reasoning-quality gap on what is a small
bucketing task (~6 categories, 3 priorities). One provider that natively handles all
three Modalities collapses the entire Content pipeline into single calls.

## Considered options

- **Gemini-only** (chosen) — native audio/doc handling, one SDK, fewest moving parts.
- **Claude + Whisper** — best-in-class text reasoning, but two providers and two
  failure modes; rejected as too much glue for the deadline.
- **Split (Gemini transcribes, Claude reasons)** — native audio plus Claude
  reasoning, but still two providers and data crossing both.

## Consequences

If classification/summarization quality becomes the thing judges scrutinize most,
the **split** option is the upgrade path. To keep that escape hatch cheap, the AI
provider must sit behind a small internal interface so transcription and reasoning
can be pointed at different providers without touching the pipeline.

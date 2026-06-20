from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ValidationError

from app.domain.models import Category, Entry, Priority

if TYPE_CHECKING:
    from google import genai

_MODEL_DEFAULT = "gemini-2.5-flash"
_FALLBACK = (Category.update, Priority.whenever)


class _Classification(BaseModel):
    category: Literal["request", "issue", "decision", "update", "question", "noise"]
    priority: Literal["now", "today", "whenever"]


class GeminiProvider:
    def __init__(self, client: genai.Client, model: str = _MODEL_DEFAULT) -> None:
        self._client = client
        self._model = model

    def classify(self, content: str) -> tuple[Category, Priority]:
        prompt = (
            "You are classifying a message from a team's operational group chat.\n\n"
            "Category — pick exactly one:\n"
            "  issue    = a problem, blocker, incident, or risk (something broken or blocking work)\n"
            "  request  = someone needs another person to DO something\n"
            "  decision = a decision made or one that needs to be made\n"
            "  update   = status/progress/FYI with no action needed\n"
            "  question = an open question waiting for an answer\n"
            "  noise    = chatter, reactions, or anything not operationally relevant\n\n"
            "Priority — pick exactly one:\n"
            "  now      = urgent, someone is blocked or it's time-sensitive TODAY\n"
            "  today    = should be handled today but not drop-everything urgent\n"
            "  whenever = no time pressure, informational or backlog\n\n"
            "Respond with JSON only, no explanation: {\"category\": \"<value>\", \"priority\": \"<value>\"}\n\n"
            f"Message: {content}"
        )
        response = self._client.models.generate_content(model=self._model, contents=prompt)
        try:
            parsed = _Classification.model_validate_json(response.text)
            return Category(parsed.category), Priority(parsed.priority)
        except (ValidationError, ValueError, Exception):
            return _FALLBACK

    def transcribe(self, audio: bytes) -> str:
        from google.genai import types
        response = self._client.models.generate_content(
            model=self._model,
            contents=[
                "Transcribe this audio exactly. Return only the transcript text.",
                types.Part.from_bytes(data=audio, mime_type="audio/ogg"),
            ],
        )
        return response.text

    def extract(self, document: bytes) -> str:
        from google.genai import types
        response = self._client.models.generate_content(
            model=self._model,
            contents=[
                types.Part.from_bytes(data=document, mime_type="application/pdf"),
                "Extract all text content from this document.",
            ],
        )
        return response.text

    def summarize(self, entries: list[Entry], draft: str) -> str:
        prompt = (
            "You are summarizing a team's daily operational digest.\n"
            "Below is a structured list of entries grouped by category and priority.\n"
            "Add a brief 'Recommended actions' section at the end based on the issues and requests.\n"
            "Keep the rest of the structure intact.\n\n"
            f"{draft}"
        )
        response = self._client.models.generate_content(model=self._model, contents=prompt)
        return response.text

import json
import os
from unittest.mock import MagicMock

import pytest

from app.domain.models import Category, Priority
from app.infrastructure.gemini_provider import GeminiProvider


def make_provider(response_text: str) -> GeminiProvider:
    """Return a GeminiProvider whose client returns a canned response."""
    mock_response = MagicMock()
    mock_response.text = response_text

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    return GeminiProvider(client=mock_client)


# --- Behavior 1: valid response parsed correctly ---

def test_classify_valid_response_returns_category_and_priority():
    provider = make_provider(json.dumps({"category": "request", "priority": "now"}))
    category, priority = provider.classify("We need access to the server urgently")
    assert category == Category.request
    assert priority == Priority.now


def test_classify_all_categories_parse():
    for cat in ["request", "issue", "decision", "update", "question", "noise"]:
        provider = make_provider(json.dumps({"category": cat, "priority": "today"}))
        category, _ = provider.classify("test content")
        assert category == Category(cat)


def test_classify_all_priorities_parse():
    for pri in ["now", "today", "whenever"]:
        provider = make_provider(json.dumps({"category": "update", "priority": pri}))
        _, priority = provider.classify("test content")
        assert priority == Priority(pri)


# --- Behavior 2: unparseable response falls back safely ---

def test_classify_non_json_response_returns_fallback():
    provider = make_provider("Sorry, I cannot classify this.")
    category, priority = provider.classify("some content")
    assert category == Category.update
    assert priority == Priority.whenever


# --- Behavior 3: valid JSON but invalid literal falls back ---

def test_classify_invalid_category_literal_returns_fallback():
    provider = make_provider(json.dumps({"category": "UNKNOWN", "priority": "now"}))
    category, priority = provider.classify("some content")
    assert category == Category.update
    assert priority == Priority.whenever


def test_classify_invalid_priority_literal_returns_fallback():
    provider = make_provider(json.dumps({"category": "request", "priority": "urgent"}))
    category, priority = provider.classify("some content")
    assert category == Category.update
    assert priority == Priority.whenever


# --- Behavior 4: transcribe returns the response text ---

def test_transcribe_returns_response_text():
    provider = make_provider("The server is down and needs immediate attention.")
    result = provider.transcribe(b"fake-ogg-bytes")
    assert result == "The server is down and needs immediate attention."


# --- Integration marker (skipped without key) ---

@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="requires GEMINI_API_KEY",
)
def test_classify_integration_returns_valid_literals():
    from google import genai
    client = genai.Client()
    provider = GeminiProvider(client=client)
    category, priority = provider.classify("The CI pipeline is broken and blocking everyone.")
    assert isinstance(category, Category)
    assert isinstance(priority, Priority)
    assert category != Category.noise  # a blocker should not be noise

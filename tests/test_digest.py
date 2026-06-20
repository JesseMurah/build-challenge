from datetime import timedelta

import pytest
from sqlmodel import Session

from app.digest.service import build_digest
from app.domain.models import Category, Entry, Modality, Priority


def make_entry(
    *,
    team_id: int = 1,
    sender_name: str = "Alice",
    category: Category,
    priority: Priority,
    content: str = "some content",
) -> Entry:
    return Entry(
        team_id=team_id,
        sender_id=1,
        sender_name=sender_name,
        modality=Modality.text,
        category=category,
        priority=priority,
        content=content,
    )


def seed(session: Session, *entries: Entry) -> None:
    for e in entries:
        session.add(e)
    session.commit()


# --- Behavior 1: grouping, ordering, attribution ---

def test_digest_groups_by_category_and_orders_by_priority(fake_provider, db_session):
    seed(
        db_session,
        make_entry(category=Category.issue,   priority=Priority.today,    content="Server slow",   sender_name="Bob"),
        make_entry(category=Category.request, priority=Priority.now,      content="Need access",   sender_name="Alice"),
        make_entry(category=Category.issue,   priority=Priority.now,      content="DB is down",    sender_name="Carol"),
        make_entry(category=Category.request, priority=Priority.whenever, content="Nice to have",  sender_name="Dave"),
    )

    result = build_digest(team_id=1, window=timedelta(hours=25), session=db_session, provider=fake_provider)

    # Category sections appear
    assert "issue" in result.lower()
    assert "request" in result.lower()
    # Priority ordering: now before today/whenever within each category
    issue_section = result[result.lower().index("issue"):]
    assert issue_section.index("DB is down") < issue_section.index("Server slow")
    # Sender attribution
    assert "Bob" in result
    assert "Alice" in result
    assert "Carol" in result
    assert "Dave" in result


# --- Behavior 2: time window exclusion ---

def test_digest_excludes_entries_outside_window(fake_provider, db_session):
    from datetime import datetime, timezone
    old_entry = Entry(
        team_id=1, sender_id=1, sender_name="Ghost",
        modality=Modality.text, category=Category.update,
        priority=Priority.whenever, content="Ancient news",
        created_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
    )
    recent = make_entry(category=Category.update, priority=Priority.today, content="Today's news", sender_name="Alice")
    seed(db_session, old_entry, recent)

    result = build_digest(team_id=1, window=timedelta(hours=25), session=db_session, provider=fake_provider)

    assert "Ancient news" not in result
    assert "Today's news" in result


# --- Behavior 3: empty window ---

def test_digest_returns_quiet_day_message_when_no_entries(fake_provider, db_session):
    result = build_digest(team_id=1, window=timedelta(hours=25), session=db_session, provider=fake_provider)

    assert result  # not empty
    assert len(result) > 0
    # Should not be an error or blank — must communicate "nothing happened"
    assert any(word in result.lower() for word in ("quiet", "nothing", "no entries", "no operational"))


# --- Behavior 4: team isolation ---

def test_digest_only_includes_entries_for_the_requested_team(fake_provider, db_session):
    seed(
        db_session,
        make_entry(team_id=1, category=Category.request, priority=Priority.now, content="Team 1 item", sender_name="Alice"),
        make_entry(team_id=2, category=Category.request, priority=Priority.now, content="Team 2 item", sender_name="Bob"),
    )

    result = build_digest(team_id=1, window=timedelta(hours=25), session=db_session, provider=fake_provider)

    assert "Team 1 item" in result
    assert "Team 2 item" not in result

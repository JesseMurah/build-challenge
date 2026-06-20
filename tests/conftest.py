import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.domain.models import Category, Priority


class FakeAIProvider:
    def __init__(self, category: Category = Category.request, priority: Priority = Priority.today):
        self._category = category
        self._priority = priority

    def classify(self, content: str) -> tuple[Category, Priority]:
        return self._category, self._priority

    def transcribe(self, audio: bytes) -> str:
        return "transcribed text"

    def extract(self, document: bytes) -> str:
        return "extracted text"

    def summarize(self, entries):
        return "summary"


@pytest.fixture
def fake_provider():
    return FakeAIProvider()


@pytest.fixture
def noise_provider():
    return FakeAIProvider(category=Category.noise, priority=Priority.whenever)


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session

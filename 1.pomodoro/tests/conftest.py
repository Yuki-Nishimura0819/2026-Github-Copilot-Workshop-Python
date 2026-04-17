import pytest

from app import create_app
from config import TestConfig
from models.repository import InMemoryRepository
from services.timer_service import TimerService


@pytest.fixture
def app():
    application = create_app(TestConfig)
    application.config.update(TESTING=True)
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_repository():
    return InMemoryRepository()


@pytest.fixture
def timer_service(mock_repository):
    return TimerService(mock_repository, TestConfig)

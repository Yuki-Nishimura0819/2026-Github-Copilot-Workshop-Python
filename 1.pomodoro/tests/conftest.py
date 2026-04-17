import pytest

from app import create_app
from config import TestConfig
from models.repository import InMemoryRepository
from services.timer_service import TimerService


_test_app = None


@pytest.fixture
def app():
    """Create a fresh test app for each test."""
    global _test_app
    _test_app = create_app(TestConfig)
    _test_app.config.update(TESTING=True)
    # Forcefully reset config to TestConfig values
    _test_app.config['WORK_DURATION'] = 10
    _test_app.config['BREAK_DURATION'] = 5
    _test_app.config['LONG_BREAK_DURATION'] = 15
    _test_app.config['SESSIONS_UNTIL_LONG_BREAK'] = 2
    return _test_app


@pytest.fixture
def client(app):
    """Create test client from app fixture."""
    return app.test_client()


@pytest.fixture
def mock_repository():
    """Create fresh in-memory repository for each test."""
    return InMemoryRepository()


@pytest.fixture
def timer_service(mock_repository):
    """Create fresh TimerService with TestConfig for each test."""
    # Create config namespace with test values
    class TestConfigObj:
        WORK_DURATION = 10
        BREAK_DURATION = 5
        LONG_BREAK_DURATION = 15
        SESSIONS_UNTIL_LONG_BREAK = 2

    return TimerService(mock_repository, TestConfigObj())

from datetime import datetime, timedelta

from services.stats_service import StatsService


def test_start_work_session_success(timer_service):
    state = timer_service.start_work_session()

    assert state["state"] == "working"
    assert state["status"] == "working"
    assert state["remaining"] == 10


def test_start_break_invalid_from_idle(timer_service):
    state = timer_service.start_break_session()

    assert "error" in state


def test_start_break_success_after_start_work(timer_service):
    timer_service.start_work_session()

    state = timer_service.start_break_session()

    assert state["state"] == "break"
    assert state["status"] == "working"
    assert state["remaining"] == 5
    assert state["completed_sessions"] == 1


def test_tick_updates_stats_on_work_completion(timer_service, mock_repository):
    timer_service.start_work_session()
    for _ in range(10):
        timer_service.tick()

    stats = StatsService(mock_repository).get_today_stats()

    assert stats["sessions"] == 1
    assert stats["total_focus_time"] == 10


def test_reset_session_returns_idle(timer_service):
    timer_service.start_work_session()

    state = timer_service.reset_session()

    assert state["state"] == "idle"
    assert state["status"] == "idle"
    assert state["remaining"] == 10


# Phase 5 & 6: StatsService enhanced tests
def test_stats_service_format_focus_time():
    """Test focus time formatting (minutes/hours)."""
    from models.repository import InMemoryRepository

    repo = InMemoryRepository()
    stats_service = StatsService(repo)

    # Less than 1 hour
    assert stats_service.format_focus_time(180) == "3分"
    assert stats_service.format_focus_time(0) == "0分"

    # 1 hour and 30 minutes
    assert stats_service.format_focus_time(5400) == "1時間30分"

    # 2 hours
    assert stats_service.format_focus_time(7200) == "2時間0分"

    # Negative (should be treated as 0)
    assert stats_service.format_focus_time(-100) == "0分"


def test_stats_service_get_today_stats_with_default_values():
    """Test that missing data returns proper defaults."""
    from models.repository import InMemoryRepository

    repo = InMemoryRepository()
    stats_service = StatsService(repo)

    stats = stats_service.get_today_stats()

    assert stats["sessions"] == 0
    assert stats["total_focus_time"] == 0
    assert stats["total_minutes"] == 0
    assert "formatted_time" in stats


def test_stats_service_get_stats_by_date():
    """Test retrieving stats for a specific date."""
    from models.repository import InMemoryRepository

    repo = InMemoryRepository()
    stats_service = StatsService(repo)

    # Save stats for a specific date
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    repo.save(f"stats:{past_date}", {"sessions": 3, "total_focus_time": 4500})

    stats = stats_service.get_stats_by_date(past_date)

    assert stats["sessions"] == 3
    assert stats["total_minutes"] == 75
    assert stats["total_hours"] == 1
    assert stats["remaining_minutes"] == 15


def test_stats_service_get_stats_by_date_invalid_format():
    """Test handling of invalid date format."""
    from models.repository import InMemoryRepository

    repo = InMemoryRepository()
    stats_service = StatsService(repo)

    stats = stats_service.get_stats_by_date("invalid-date")

    assert "error" in stats


def test_stats_service_get_week_stats():
    """Test aggregating stats for the past 7 days."""
    from models.repository import InMemoryRepository

    repo = InMemoryRepository()
    stats_service = StatsService(repo)

    # Save stats for a few days
    today = datetime.now()
    for i in range(3):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        repo.save(f"stats:{date}", {"sessions": 2, "total_focus_time": 3000})

    stats = stats_service.get_week_stats()

    assert stats["total_sessions"] == 6
    assert stats["total_focus_time"] == 9000
    assert "completion_rate" in stats
    assert "average_focus_time" in stats
    assert "chart_data" in stats


def test_stats_service_gamification_fields():
    """Test XP/level/streak/badges fields in today's stats."""
    from models.repository import InMemoryRepository

    repo = InMemoryRepository()
    stats_service = StatsService(repo)

    today = datetime.now()
    for i in range(3):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        repo.save(f"stats:{date}", {"sessions": 4, "total_focus_time": 2400})

    stats = stats_service.get_today_stats()

    assert stats["xp"] >= 0
    assert stats["level"] >= 1
    assert stats["streak_days"] == 3
    assert "badges" in stats
    assert any(badge["id"] == "streak_3" and badge["achieved"] for badge in stats["badges"])


def test_stats_service_get_month_stats():
    """Test monthly statistics aggregation."""
    from models.repository import InMemoryRepository

    repo = InMemoryRepository()
    stats_service = StatsService(repo)

    today = datetime.now()
    for i in range(5):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        repo.save(f"stats:{date}", {"sessions": 2, "total_focus_time": 1800})

    stats = stats_service.get_month_stats()

    assert stats["total_sessions"] == 10
    assert stats["total_focus_time"] == 9000
    assert "completion_rate" in stats
    assert "chart_data" in stats


def test_long_break_activation(timer_service):
    """Test that long break is triggered at the right session count."""
    # Mock config with SESSIONS_UNTIL_LONG_BREAK = 2
    timer_service.config.SESSIONS_UNTIL_LONG_BREAK = 2
    timer_service.config.LONG_BREAK_DURATION = 15

    # Complete 2 work sessions
    for _ in range(2):
        timer_service.start_work_session()
        for _ in range(10):
            timer_service.tick()
        timer_service.start_break_session()

    # Next break should be long break
    duration = timer_service._get_break_duration()
    assert duration == 15


def test_long_break_normal_rhythm(timer_service):
    """Test long break rhythm (not every break)."""
    timer_service.config.SESSIONS_UNTIL_LONG_BREAK = 3
    timer_service.config.LONG_BREAK_DURATION = 15
    timer_service.config.BREAK_DURATION = 5

    # After 0 sessions (completed_sessions = 0): normal break
    timer_service.state_machine.completed_sessions = 0
    duration = timer_service._get_break_duration()
    assert duration == 5

    # After 1 session (completed_sessions = 1): normal break
    timer_service.state_machine.completed_sessions = 1
    duration = timer_service._get_break_duration()
    assert duration == 5

    # After 2 sessions (completed_sessions = 2): normal break
    timer_service.state_machine.completed_sessions = 2
    duration = timer_service._get_break_duration()
    assert duration == 5

    # After 3 sessions (completed_sessions = 3): long break
    timer_service.state_machine.completed_sessions = 3
    duration = timer_service._get_break_duration()
    assert duration == 15

    # After 4 sessions (completed_sessions = 4): normal break again
    timer_service.state_machine.completed_sessions = 4
    duration = timer_service._get_break_duration()
    assert duration == 5

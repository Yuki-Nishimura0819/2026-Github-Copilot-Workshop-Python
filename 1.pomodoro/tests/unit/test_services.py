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

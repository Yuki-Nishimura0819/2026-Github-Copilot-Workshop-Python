from models.session import SessionState, SessionStateMachine


def test_start_work_from_idle():
    machine = SessionStateMachine()

    changed = machine.start_work()

    assert changed is True
    assert machine.state == SessionState.WORKING


def test_start_break_from_working_increments_count():
    machine = SessionStateMachine()
    machine.start_work()

    changed = machine.start_break()

    assert changed is True
    assert machine.state == SessionState.BREAK
    assert machine.completed_sessions == 1


def test_invalid_transition_break_from_idle_is_rejected():
    machine = SessionStateMachine()

    changed = machine.start_break()

    assert changed is False
    assert machine.state == SessionState.IDLE
    assert machine.completed_sessions == 0


def test_start_work_from_break_is_allowed():
    machine = SessionStateMachine()
    machine.start_work()
    machine.start_break()

    changed = machine.start_work()

    assert changed is True
    assert machine.state == SessionState.WORKING


def test_reset_sets_state_to_idle():
    machine = SessionStateMachine()
    machine.start_work()

    machine.reset()

    assert machine.state == SessionState.IDLE

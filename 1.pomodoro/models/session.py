from enum import Enum


class SessionState(Enum):
    IDLE = "idle"
    WORKING = "working"
    BREAK = "break"


class SessionStateMachine:
    """Explicit state transitions for work/break sessions."""

    def __init__(self):
        self.state = SessionState.IDLE
        self.completed_sessions = 0

    def start_work(self) -> bool:
        if self.state in (SessionState.IDLE, SessionState.BREAK):
            self.state = SessionState.WORKING
            return True
        return False

    def start_break(self) -> bool:
        if self.state == SessionState.WORKING:
            self.state = SessionState.BREAK
            self.completed_sessions += 1
            return True
        return False

    def reset(self) -> None:
        self.state = SessionState.IDLE

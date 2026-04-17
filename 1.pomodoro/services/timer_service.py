from __future__ import annotations

from datetime import datetime

from models.repository import Repository
from models.session import SessionState, SessionStateMachine
from models.timer import Timer


class TimerService:
    """Orchestrates timer behavior and state transitions."""

    def __init__(self, repository: Repository, config):
        self.repository = repository
        self.config = config
        self.timer = Timer(config.WORK_DURATION)
        self.state_machine = SessionStateMachine()

    def start_work_session(self) -> dict:
        if not self.state_machine.start_work():
            return {"error": "無効な状態遷移"}

        self.timer = Timer(self.config.WORK_DURATION)
        self.timer.start()
        return self.get_current_state()

    def start_break_session(self) -> dict:
        if not self.state_machine.start_break():
            return {"error": "無効な状態遷移"}

        self.timer = Timer(self.config.BREAK_DURATION)
        self.timer.start()
        return self.get_current_state()

    def tick(self) -> dict:
        if self.timer.status != "working":
            return self.get_current_state()

        before = self.timer.remaining
        after = self.timer.tick()

        if before > 0 and after == 0:
            self._handle_session_complete()
            self.timer.status = "idle"

        return self.get_current_state()

    def reset_session(self) -> dict:
        self.state_machine.reset()
        self.timer = Timer(self.config.WORK_DURATION)
        return self.get_current_state()

    def get_current_state(self) -> dict:
        return {
            "remaining": self.timer.remaining,
            "status": self.timer.status,
            "state": self.state_machine.state.value,
            "completed_sessions": self.state_machine.completed_sessions,
        }

    def _handle_session_complete(self) -> None:
        # Count only completed work sessions as focus statistics.
        if self.state_machine.state != SessionState.WORKING:
            return

        today = datetime.now().strftime("%Y-%m-%d")
        key = f"stats:{today}"
        stats = self.repository.load(key) or {"sessions": 0, "total_focus_time": 0}
        stats["sessions"] += 1
        stats["total_focus_time"] += self.config.WORK_DURATION
        self.repository.save(key, stats)

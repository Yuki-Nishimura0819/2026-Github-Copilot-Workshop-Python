from __future__ import annotations

from datetime import datetime

from models.repository import Repository


class StatsService:
    """Provides statistics retrieval helpers."""

    def __init__(self, repository: Repository):
        self.repository = repository

    def get_today_stats(self) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"stats:{today}"
        return self.repository.load(key) or {"sessions": 0, "total_focus_time": 0}

from __future__ import annotations

from datetime import datetime, timedelta

from models.repository import Repository


class StatsService:
    """Provides statistics retrieval and formatting helpers."""

    def __init__(self, repository: Repository):
        self.repository = repository

    def get_today_stats(self) -> dict:
        """Get today's statistics with proper formatting."""
        today = datetime.now().strftime("%Y-%m-%d")
        stats = self._load_stats(today)
        return self._format_stats(stats)

    def _load_stats(self, date_str: str) -> dict:
        """Load raw statistics for the given date."""
        key = f"stats:{date_str}"
        data = self.repository.load(key)
        if data is None:
            return {"sessions": 0, "total_focus_time": 0}
        # Ensure default structure
        return {
            "sessions": max(0, int(data.get("sessions", 0))),
            "total_focus_time": max(0, int(data.get("total_focus_time", 0))),
        }

    def _format_stats(self, stats: dict) -> dict:
        """Format statistics with multiple display units."""
        total_seconds = stats["total_focus_time"]
        total_minutes = total_seconds // 60
        total_hours = total_minutes // 60
        remaining_minutes = total_minutes % 60

        return {
            "sessions": stats["sessions"],
            "total_focus_time": total_seconds,
            "total_minutes": total_minutes,
            "total_hours": total_hours,
            "remaining_minutes": remaining_minutes,
            "formatted_time": self.format_focus_time(total_seconds),
        }

    def format_focus_time(self, seconds: int) -> str:
        """Format seconds to human-readable time."""
        if seconds < 0:
            seconds = 0
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}分"
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}時間{mins}分"

    def get_stats_by_date(self, date_str: str) -> dict:
        """Get statistics for a specific date (YYYY-MM-DD format)."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return {
                "error": f"Invalid date format: {date_str}. Use YYYY-MM-DD",
                "sessions": 0,
                "total_focus_time": 0,
            }
        stats = self._load_stats(date_str)
        return self._format_stats(stats)

    def get_week_stats(self) -> dict:
        """Get statistics for the past 7 days."""
        week_data = {}
        total_sessions = 0
        total_focus_time = 0

        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self._load_stats(date)
            week_data[date] = stats
            total_sessions += stats["sessions"]
            total_focus_time += stats["total_focus_time"]

        return {
            "daily": week_data,
            "total_sessions": total_sessions,
            "total_focus_time": total_focus_time,
            "formatted_time": self.format_focus_time(total_focus_time),
        }

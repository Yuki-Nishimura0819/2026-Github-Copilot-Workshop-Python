from __future__ import annotations

from datetime import datetime, timedelta

from models.repository import Repository

XP_PER_SESSION = 100
XP_PER_LEVEL = 500
WEEKLY_BADGE_TARGET = 10
STREAK_BADGE_TARGET = 3
EXPECTED_SESSIONS_PER_DAY = 8


class StatsService:
    """Provides statistics retrieval and formatting helpers."""

    def __init__(self, repository: Repository):
        self.repository = repository
        self._gamification_cache = {
            "date": None,
            "total_sessions": 0,
            "streak_days": 0,
        }

    def get_today_stats(self) -> dict:
        """Get today's statistics with proper formatting."""
        today = datetime.now().strftime("%Y-%m-%d")
        stats = self._load_stats(today)
        formatted = self._format_stats(stats)

        if self._gamification_cache["date"] != today:
            self._gamification_cache = {
                "date": today,
                "total_sessions": self._get_total_sessions(days=365),
                "streak_days": self._calculate_streak(),
            }

        total_sessions = self._gamification_cache["total_sessions"]
        streak_days = self._gamification_cache["streak_days"]
        week_stats = self.get_week_stats()

        formatted.update({
            "xp": total_sessions * XP_PER_SESSION,
            "level": (total_sessions * XP_PER_SESSION) // XP_PER_LEVEL + 1,
            "streak_days": streak_days,
            "badges": self._calculate_badges(streak_days, week_stats["total_sessions"]),
        })
        return formatted

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
        chart_data = []
        total_sessions = 0
        total_focus_time = 0

        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self._load_stats(date)
            week_data[date] = stats
            chart_data.append({
                "date": date,
                "sessions": stats["sessions"],
                "total_focus_time": stats["total_focus_time"],
            })
            total_sessions += stats["sessions"]
            total_focus_time += stats["total_focus_time"]

        average_focus_time_per_session = total_focus_time / total_sessions if total_sessions > 0 else 0
        completion_rate = min(
            100.0,
            (total_sessions / (7 * EXPECTED_SESSIONS_PER_DAY)) * 100,
        )

        return {
            "daily": week_data,
            "total_sessions": total_sessions,
            "total_focus_time": total_focus_time,
            "average_focus_time": round(average_focus_time_per_session, 2),
            "completion_rate": round(completion_rate, 2),
            "chart_data": list(reversed(chart_data)),
            "formatted_time": self.format_focus_time(total_focus_time),
        }

    def get_month_stats(self) -> dict:
        """Get statistics for the past 30 days."""
        return self._get_period_stats(30)

    def _get_period_stats(self, days: int) -> dict:
        period_data = {}
        chart_data = []
        total_sessions = 0
        total_focus_time = 0

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            stats = self._load_stats(date)
            period_data[date] = stats
            chart_data.append({
                "date": date,
                "sessions": stats["sessions"],
                "total_focus_time": stats["total_focus_time"],
            })
            total_sessions += stats["sessions"]
            total_focus_time += stats["total_focus_time"]

        average_focus_time_per_session = total_focus_time / total_sessions if total_sessions > 0 else 0
        completion_rate = min(
            100.0,
            (total_sessions / (days * EXPECTED_SESSIONS_PER_DAY)) * 100,
        )

        return {
            "daily": period_data,
            "total_sessions": total_sessions,
            "total_focus_time": total_focus_time,
            "average_focus_time": round(average_focus_time_per_session, 2),
            "completion_rate": round(completion_rate, 2),
            "chart_data": list(reversed(chart_data)),
            "formatted_time": self.format_focus_time(total_focus_time),
        }

    def _calculate_streak(self) -> int:
        streak = 0
        for i in range(365):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if self._load_stats(date)["sessions"] > 0:
                streak += 1
            else:
                break
        return streak

    def _get_total_sessions(self, days: int) -> int:
        total_sessions = 0
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            total_sessions += self._load_stats(date)["sessions"]
        return total_sessions

    def _calculate_badges(self, streak_days: int, weekly_sessions: int) -> list[dict]:
        return [
            {
                "id": "streak_3",
                "title": "3日連続",
                "description": "3日連続で1回以上ポモドーロを完了",
                "achieved": streak_days >= STREAK_BADGE_TARGET,
            },
            {
                "id": "weekly_10",
                "title": "今週10回完了",
                "description": "1週間で10回以上ポモドーロを完了",
                "achieved": weekly_sessions >= WEEKLY_BADGE_TARGET,
            },
        ]

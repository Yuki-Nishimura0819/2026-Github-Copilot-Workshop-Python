from flask import Flask, jsonify, render_template, request

from config import DevelopmentConfig
from models.repository import FileRepository, InMemoryRepository
from services.stats_service import StatsService
from services.timer_service import TimerService


def create_app(config_object=None):
    """Application factory for environment-based startup."""

    app = Flask(__name__)
    if config_object is None:
        config_object = DevelopmentConfig

    app.config.from_object(config_object)

    if config_object.REPOSITORY_TYPE == "memory":
        repository = InMemoryRepository()
    else:
        repository = FileRepository()

    timer_service = TimerService(repository, config_object)
    stats_service = StatsService(repository)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/timer/start-work")
    def start_work():
        state = timer_service.start_work_session()
        status_code = 400 if "error" in state else 200
        return jsonify(state), status_code

    @app.post("/api/timer/start-break")
    def start_break():
        state = timer_service.start_break_session()
        status_code = 400 if "error" in state else 200
        return jsonify(state), status_code

    @app.get("/api/timer/state")
    def get_state():
        return jsonify(timer_service.get_current_state())

    @app.post("/api/timer/tick")
    def tick():
        return jsonify(timer_service.tick())

    @app.post("/api/timer/reset")
    def reset():
        return jsonify(timer_service.reset_session())

    @app.get("/api/stats/today")
    def get_today_stats():
        return jsonify(stats_service.get_today_stats())

    @app.get("/api/stats/week")
    def get_week_stats():
        return jsonify(stats_service.get_week_stats())

    @app.get("/api/stats/month")
    def get_month_stats():
        return jsonify(stats_service.get_month_stats())

    @app.get("/api/stats/date/<date_str>")
    def get_stats_by_date(date_str):
        stats = stats_service.get_stats_by_date(date_str)
        status_code = 400 if "error" in stats else 200
        return jsonify(stats), status_code

    # Configuration API (Phase 6)
    @app.get("/api/config")
    def get_config():
        return jsonify({
            "work_duration": app.config.get("WORK_DURATION", 1500),
            "break_duration": app.config.get("BREAK_DURATION", 300),
            "long_break_duration": app.config.get("LONG_BREAK_DURATION", 900),
            "sessions_until_long_break": app.config.get("SESSIONS_UNTIL_LONG_BREAK", 4),
        })

    @app.post("/api/config")
    def update_config():
        data = request.get_json() or {}
        # Validate and update configuration
        if "work_duration" in data:
            val = int(data.get("work_duration", 0))
            if 60 <= val <= 3600:
                app.config["WORK_DURATION"] = val
                timer_service.config.WORK_DURATION = val
        if "break_duration" in data:
            val = int(data.get("break_duration", 0))
            if 60 <= val <= 1800:
                app.config["BREAK_DURATION"] = val
                timer_service.config.BREAK_DURATION = val
        if "long_break_duration" in data:
            val = int(data.get("long_break_duration", 0))
            if 300 <= val <= 3600:
                app.config["LONG_BREAK_DURATION"] = val
        if "sessions_until_long_break" in data:
            val = int(data.get("sessions_until_long_break", 0))
            if 1 <= val <= 10:
                app.config["SESSIONS_UNTIL_LONG_BREAK"] = val

        return jsonify({"status": "updated"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=app.config.get("DEBUG", False))

from flask import Flask, jsonify, render_template

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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))

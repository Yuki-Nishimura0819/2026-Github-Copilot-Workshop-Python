class Timer:
    """Core timer logic with minimal side effects."""

    def __init__(self, initial_seconds: int):
        if initial_seconds < 0:
            raise ValueError("initial_seconds must be >= 0")

        self.initial_seconds = initial_seconds
        self.remaining = initial_seconds
        self.status = "idle"

    def tick(self) -> int:
        """Advance one second when running and return remaining seconds."""
        if self.status == "working" and self.remaining > 0:
            self.remaining -= 1
        return self.remaining

    def start(self) -> None:
        self.status = "working"

    def pause(self) -> None:
        self.status = "paused"

    def reset(self) -> None:
        self.remaining = self.initial_seconds
        self.status = "idle"

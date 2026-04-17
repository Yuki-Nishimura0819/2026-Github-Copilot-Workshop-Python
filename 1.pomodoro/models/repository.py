from __future__ import annotations

from abc import ABC, abstractmethod
import json
from pathlib import Path


class Repository(ABC):
    """Abstract storage contract for application state/statistics."""

    @abstractmethod
    def save(self, key: str, data: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, key: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError


class FileRepository(Repository):
    """JSON file-backed repository for local persistence."""

    def __init__(self, filepath: str = "sessions.json"):
        self.filepath = Path(filepath)

    def _read_all(self) -> dict:
        if not self.filepath.exists():
            return {}

        with self.filepath.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_all(self, data: dict) -> None:
        with self.filepath.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def save(self, key: str, data: dict) -> None:
        all_data = self._read_all()
        all_data[key] = data
        self._write_all(all_data)

    def load(self, key: str) -> dict:
        all_data = self._read_all()
        return all_data.get(key, {})

    def delete(self, key: str) -> None:
        all_data = self._read_all()
        all_data.pop(key, None)
        self._write_all(all_data)


class InMemoryRepository(Repository):
    """In-memory repository primarily used for tests."""

    def __init__(self):
        self.storage: dict[str, dict] = {}

    def save(self, key: str, data: dict) -> None:
        self.storage[key] = data

    def load(self, key: str) -> dict:
        return self.storage.get(key, {})

    def delete(self, key: str) -> None:
        self.storage.pop(key, None)

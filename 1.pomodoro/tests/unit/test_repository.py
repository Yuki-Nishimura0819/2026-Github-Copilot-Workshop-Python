from models.repository import FileRepository, InMemoryRepository


def test_in_memory_repository_save_load_delete():
    repo = InMemoryRepository()

    repo.save("today", {"sessions": 1})
    assert repo.load("today") == {"sessions": 1}

    repo.delete("today")
    assert repo.load("today") == {}


def test_file_repository_save_load_delete(tmp_path):
    filepath = tmp_path / "sessions.json"
    repo = FileRepository(str(filepath))

    repo.save("today", {"sessions": 2})
    assert repo.load("today") == {"sessions": 2}

    repo.delete("today")
    assert repo.load("today") == {}


def test_file_repository_load_missing_key_returns_empty(tmp_path):
    filepath = tmp_path / "sessions.json"
    repo = FileRepository(str(filepath))

    assert repo.load("missing") == {}

def test_start_work_endpoint(client):
    response = client.post("/api/timer/start-work")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["state"] == "working"
    assert payload["remaining"] == 10


def test_start_break_invalid_transition(client):
    response = client.post("/api/timer/start-break")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_tick_endpoint_changes_remaining(client):
    client.post("/api/timer/start-work")

    response = client.post("/api/timer/tick")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["remaining"] == 9


def test_reset_endpoint(client):
    client.post("/api/timer/start-work")
    response = client.post("/api/timer/reset")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["state"] == "idle"
    assert payload["status"] == "idle"
    assert payload["remaining"] == 10


def test_today_stats_default_and_after_completion(client):
    first = client.get("/api/stats/today")
    first_payload = first.get_json()
    assert first_payload["sessions"] == 0
    assert first_payload["total_focus_time"] == 0

    client.post("/api/timer/start-work")
    for _ in range(10):
        client.post("/api/timer/tick")

    second = client.get("/api/stats/today")
    second_payload = second.get_json()
    assert second_payload["sessions"] == 1
    assert second_payload["total_focus_time"] == 10

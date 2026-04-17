def test_index_page_returns_200(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "ポモドーロタイマー" in response.get_data(as_text=True)

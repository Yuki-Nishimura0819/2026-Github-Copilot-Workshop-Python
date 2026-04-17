def test_index_page_returns_200(client):
    response = client.get("/")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "ポモドーロタイマー" in html
    assert 'id="ringWrap"' in html
    assert 'id="focusEffect"' in html

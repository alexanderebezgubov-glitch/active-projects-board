"""Маршруты через TestClient. / HTTP routes via TestClient.

Стартовый хук приложения создаёт пользователя admin/admin и таблицы.
The app startup hook seeds admin/admin and the tables.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_login_required_and_board_accessible():
    with TestClient(app) as client:
        # без входа доска редиректит на /login / unauthenticated board redirects
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 303

        # вход admin/admin / sign in
        resp = client.post(
            "/login", data={"username": "admin", "password": "admin"}, follow_redirects=False
        )
        assert resp.status_code == 303

        board = client.get("/")
        assert board.status_code == 200
        assert "Доска" in board.text or "Board" in board.text


def test_language_switch():
    with TestClient(app) as client:
        client.post("/login", data={"username": "admin", "password": "admin"})
        client.get("/set-lang/en")
        board = client.get("/")
        assert "Next deadline" in board.text


def test_template_download():
    with TestClient(app) as client:
        client.post("/login", data={"username": "admin", "password": "admin"})
        resp = client.get("/import/template.csv")
        assert resp.status_code == 200
        assert "project,stage" in resp.text

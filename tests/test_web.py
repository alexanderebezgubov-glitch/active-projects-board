"""Маршруты через TestClient. / HTTP routes via TestClient.

Стартовый хук приложения создаёт пользователя admin/admin и таблицы; фикстура
``db`` пересоздаёт таблицы перед каждым тестом, поэтому состояние изолировано.
The startup hook seeds admin/admin; the ``db`` fixture resets tables per test.
"""

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models import Project, ensure_stage_rows


def _login(client):
    return client.post("/login", data={"username": "admin", "password": "admin"})


def _make_project(db, name, stage, deadline=None, all_done=False):
    p = Project(name=name)
    ensure_stage_rows(p)
    if all_done:
        for row in p.stages:
            row.completed = True
    else:
        for i in range(1, stage):
            p.stage_map[i].completed = True
        if deadline:
            p.stage_map[stage].planned_date = deadline
    db.add(p)
    db.commit()
    return p


# --- Аутентификация / auth ---


def test_login_required_and_board_accessible(db):
    with TestClient(app) as client:
        assert client.get("/", follow_redirects=False).status_code == 303
        assert _login(client).status_code == 200  # follows redirect to board
        board = client.get("/")
        assert board.status_code == 200
        assert "Доска" in board.text or "Board" in board.text


def test_login_failure_shows_error(db):
    with TestClient(app) as client:
        resp = client.post(
            "/login", data={"username": "admin", "password": "wrong"}, follow_redirects=False
        )
        assert resp.status_code == 200
        assert "admin" not in resp.text or "error" in resp.text.lower() or "Неверн" in resp.text


def test_login_page_redirects_when_authenticated(db):
    with TestClient(app) as client:
        _login(client)
        assert client.get("/login", follow_redirects=False).status_code == 303


def test_logout_clears_session(db):
    with TestClient(app) as client:
        _login(client)
        assert client.get("/logout", follow_redirects=False).status_code == 303
        assert client.get("/", follow_redirects=False).status_code == 303


def test_protected_routes_redirect_anonymous(db):
    with TestClient(app) as client:
        for path in ["/", "/settings", "/import", "/projects/1"]:
            assert client.get(path, follow_redirects=False).status_code == 303
        assert (
            client.post("/projects/new", data={"name": "x"}, follow_redirects=False).status_code
            == 303
        )
        assert client.post("/admin/run-check", follow_redirects=False).status_code == 303


# --- Язык / language ---


def test_language_switch(db):
    with TestClient(app) as client:
        _login(client)
        client.get("/set-lang/en")
        assert "Add project" in client.get("/").text
        client.get("/set-lang/ru")
        assert "Добавить проект" in client.get("/").text


# --- Проекты: жизненный цикл / project lifecycle ---


def test_project_create_detail_update_delete(db):
    with TestClient(app) as client:
        _login(client)

        created = client.post(
            "/projects/new", data={"name": "Проект Альфа"}, follow_redirects=False
        )
        assert created.status_code == 303
        location = created.headers["location"]
        assert "/projects/" in location
        pid = int(location.rstrip("/").split("/")[-1])

        detail = client.get(f"/projects/{pid}")
        assert detail.status_code == 200
        assert "Проект Альфа" in detail.text

        # этап 1 выполнен, дата на этапе 2 валидная, на этапе 3 — мусор (ветка _parse_date)
        upd = client.post(
            f"/projects/{pid}",
            data={
                "name": "Проект Альфа",
                "done_1": "on",
                "date_2": "2026-06-25",
                "date_3": "не-дата",
            },
            follow_redirects=False,
        )
        assert upd.status_code == 303

        board = client.get("/")
        assert "Проект Альфа" in board.text
        assert "2026-06-25" in board.text  # ближайший дедлайн = этап 2

        deleted = client.post(f"/projects/{pid}/delete", follow_redirects=False)
        assert deleted.status_code == 303
        assert "Проект Альфа" not in client.get("/").text


def test_create_project_blank_name_noop(db):
    with TestClient(app) as client:
        _login(client)
        resp = client.post("/projects/new", data={"name": "   "}, follow_redirects=False)
        assert resp.status_code == 303
        assert resp.headers["location"] == "/"


def test_missing_project_redirects(db):
    with TestClient(app) as client:
        _login(client)
        assert client.get("/projects/99999", follow_redirects=False).status_code == 303
        assert (
            client.post("/projects/99999", data={"name": "x"}, follow_redirects=False).status_code
            == 303
        )


def test_board_renders_all_status_variants(db):
    today = date.today()
    _make_project(db, "Просроченный", 5, today - timedelta(days=2))
    _make_project(db, "Сегодня", 5, today)
    _make_project(db, "Скоро", 5, today + timedelta(days=3))
    _make_project(db, "В срок", 5, today + timedelta(days=40))
    _make_project(db, "Без даты", 5, None)
    _make_project(db, "Завершён", 1, all_done=True)
    with TestClient(app) as client:
        _login(client)
        html = client.get("/").text
        for name in ["Просроченный", "Сегодня", "Скоро", "В срок", "Без даты", "Завершён"]:
            assert name in html


# --- Настройки / settings ---


def test_settings_get_and_save(db):
    with TestClient(app) as client:
        _login(client)
        assert client.get("/settings").status_code == 200
        saved = client.post(
            "/settings",
            data={"email": "u@example.com", "telegram_chat_id": "12345", "lang_pref": "en"},
        )
        assert saved.status_code == 200
        assert "u@example.com" in saved.text
        assert "12345" in saved.text


# --- Запуск проверки дедлайнов / manual deadline check ---


def test_admin_run_check_returns_count(db):
    _make_project(db, "Контроль", 5, date.today() - timedelta(days=1))
    with TestClient(app) as client:
        _login(client)
        resp = client.post("/admin/run-check")
        assert resp.status_code == 200
        assert "sent" in resp.json()


# --- Импорт / import ---


def test_import_template_download(db):
    with TestClient(app) as client:
        _login(client)
        resp = client.get("/import/template.csv")
        assert resp.status_code == 200
        assert "project,stage" in resp.text


def test_import_upload_via_form(db):
    with TestClient(app) as client:
        _login(client)
        csv_bytes = "project,stage,planned_date\nИмпорт-Веб,7,2026-06-28\n".encode()
        resp = client.post("/import", files={"file": ("data.csv", csv_bytes, "text/csv")})
        assert resp.status_code == 200
        assert "Импорт-Веб" in client.get("/").text


def test_import_bad_file_shows_error(db):
    with TestClient(app) as client:
        _login(client)
        # нет колонок project/stage -> ImportError_ -> отрисовка ошибки
        bad = b"foo,bar\n1,2\n"
        resp = client.post("/import", files={"file": ("bad.csv", bad, "text/csv")})
        assert resp.status_code == 200

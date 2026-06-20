# Contributing / Разработка

Спасибо за вклад! Ниже — как поднять окружение и **запустить тесты локально**.
Thanks for contributing! Here's how to set up and **run the tests locally**.

## Окружение / Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt   # рантайм + pytest / runtime + pytest
```

`requirements-dev.txt` подтягивает рабочие зависимости и `pytest`.
`requirements-dev.txt` pulls in the runtime deps plus `pytest`.

## Запуск тестов / Running tests

Из корня проекта / from the project root:

```bash
pytest                       # весь набор / the whole suite
pytest -v                    # подробный вывод / verbose
pytest tests/test_importer.py            # один файл / a single file
pytest tests/test_stages.py::test_next_deadline_skips_completed_and_undated  # один тест / one test
pytest -k import             # по подстроке имени / by name substring
pytest --cov=app --cov-report=term-missing   # покрытие / coverage (as in CI)
# CI требует покрытие ≥ 70% (--cov-fail-under=70). / CI requires coverage ≥ 70%.
```

Ожидаемо: `14 passed`. / Expected: `14 passed`.

## Линтер / Linting

Код проверяется линтером **ruff** (конфиг — `ruff.toml`). Те же проверки гоняет CI.
Code is linted with **ruff** (config in `ruff.toml`); CI runs the same checks.

```bash
ruff check .          # проверить / check
ruff check --fix .    # автоисправления / auto-fix
ruff format .         # отформатировать / format
ruff format --check . # проверить формат (как в CI) / verify formatting (CI does this)
```

Перед PR убедитесь, что `ruff check .` и `pytest` проходят.
Before a PR, make sure both `ruff check .` and `pytest` pass.

### Что важно знать / Good to know

- Тесты **изолированы**: `tests/conftest.py` указывает `DATABASE_URL` на временную
  SQLite-базу **до** импорта приложения, поэтому рабочая `project_board.db` не
  затрагивается. Сеть не используется — Telegram/SMTP в тестах отключены
  (пустые `TELEGRAM_BOT_TOKEN`/`SMTP_HOST`).
- Tests are **isolated**: `tests/conftest.py` points `DATABASE_URL` at a temp
  SQLite DB **before** the app is imported, so your real `project_board.db` is
  never touched. No network is used — Telegram/SMTP are disabled in tests.
- Фикстура `db` пересоздаёт таблицы перед каждым тестом. / The `db` fixture
  recreates tables before each test.
- Запускать `pytest` нужно из корня репозитория, чтобы пакет `app` импортировался.
  Run `pytest` from the repo root so the `app` package resolves.

## Покрытие / What's covered

| Файл / File              | Что проверяет / What it checks                              |
|--------------------------|-------------------------------------------------------------|
| `tests/test_stages.py`   | каталог 29 этапов, текущий этап, расчёт ближайшего дедлайна  |
| `tests/test_importer.py` | разбор CSV/Excel, обновление по имени, ошибки строк          |
| `tests/test_scheduler.py`| детекция дедлайнов и дедупликация пингов                     |
| `tests/test_web.py`      | вход/авторизация, переключение языка, скачивание шаблона     |

Добавляете фичу — добавьте тест рядом и убедитесь, что `pytest` зелёный перед PR.
Adding a feature — add a test next to it and make sure `pytest` is green before a PR.

## Стиль / Style

- Двуязычные строки интерфейса — в `app/i18n.py` (ключ + RU/EN). Не хардкодьте
  текст в шаблонах. / Bilingual UI strings live in `app/i18n.py` — don't hardcode
  text in templates.
- 29 этапов — единый источник в `app/stages.py`. / The 29 stages have one source
  of truth in `app/stages.py`.
- Комментарии и сообщения — на русском и английском, как в остальном коде.
  Comments and messages are bilingual, matching the existing code.

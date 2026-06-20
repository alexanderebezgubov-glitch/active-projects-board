"""Тестовое окружение: изолированная временная БД. / Test setup: isolated temp DB.

Переменные окружения выставляются ДО импорта модулей приложения, чтобы
``app.config`` подхватил тестовую базу, а не рабочую.
"""

import os
import tempfile

os.environ["SECRET_KEY"] = "test-secret"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("SMTP_HOST", "")

import pytest  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture()
def db():
    """Чистая БД на каждый тест. / A fresh database per test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

"""Конфигурация приложения из переменных окружения. / App configuration from env vars."""

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _days(value: str | None) -> list[int]:
    if not value:
        return [7, 3, 1]
    out: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return sorted(set(out), reverse=True) or [7, 3, 1]


SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./project_board.db")

REMINDER_DAYS_BEFORE = _days(os.getenv("REMINDER_DAYS_BEFORE"))
DAILY_CHECK_TIME = os.getenv("DAILY_CHECK_TIME", "09:00")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@example.com").strip()
SMTP_USE_TLS = _bool(os.getenv("SMTP_USE_TLS"), True)

DEFAULT_LANG = "ru"

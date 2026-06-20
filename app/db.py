"""Подключение к базе и сессии SQLAlchemy. / Database engine and sessions."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Iterator[Session]:
    """FastAPI dependency: per-request DB session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    from . import models  # noqa: F401  (register models)

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite()


# Колонки, добавленные после первого релиза. SQLite не умеет добавлять их через
# create_all, поэтому досоздаём вручную. / Columns added post-release; SQLite
# won't add them via create_all, so we ALTER them in.
_ADDED_COLUMNS = {
    "projects": {
        "final_deadline": "DATE",
        "channel": "VARCHAR(16) DEFAULT 'telegram'",
        "contact": "VARCHAR(128)",
    },
}


def _migrate_sqlite() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return
    from sqlalchemy import text

    with engine.begin() as conn:
        for table, cols in _ADDED_COLUMNS.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            for name, ddl in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))

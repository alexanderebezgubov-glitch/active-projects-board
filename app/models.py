"""Модели данных. / Data models.

Этапы (29 шт.) — это фиксированный справочник в ``stages.py``; в БД хранится
прогресс каждого проекта по этим этапам (плановая дата + отметка о выполнении).

The 29 stages are a fixed catalog in ``stages.py``; the DB stores each
project's progress over those stages (planned date + completion flag).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base
from .stages import STAGE_COUNT, STAGES


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), default=None)
    lang: Mapped[str] = mapped_column(String(2), default="ru")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    stages: Mapped[list[ProjectStage]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectStage.stage_index",
    )

    # --- Производные свойства / derived properties ---

    @property
    def stage_map(self) -> dict[int, ProjectStage]:
        return {s.stage_index: s for s in self.stages}

    @property
    def current_stage_index(self) -> int | None:
        """Первый незавершённый этап. / First incomplete stage. None if all done."""
        sm = self.stage_map
        for i in range(1, STAGE_COUNT + 1):
            row = sm.get(i)
            if row is None or not row.completed:
                return i
        return None

    @property
    def completed_count(self) -> int:
        return sum(1 for s in self.stages if s.completed)

    @property
    def next_deadline(self) -> date | None:
        """Плановая дата ближайшего незавершённого этапа, у которого она задана.

        Planned date of the nearest incomplete stage that has one set.
        """
        sm = self.stage_map
        idx = self.current_stage_index
        if idx is None:
            return None
        for i in range(idx, STAGE_COUNT + 1):
            row = sm.get(i)
            if row and not row.completed and row.planned_date:
                return row.planned_date
        return None


class ProjectStage(Base):
    __tablename__ = "project_stages"
    __table_args__ = (UniqueConstraint("project_id", "stage_index", name="uq_project_stage"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    stage_index: Mapped[int] = mapped_column(Integer)
    planned_date: Mapped[date | None] = mapped_column(Date, default=None)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    project: Mapped[Project] = relationship(back_populates="stages")


class ReminderLog(Base):
    """Чтобы не слать один и тот же пинг дважды. / Dedup sent reminders."""

    __tablename__ = "reminder_log"
    __table_args__ = (
        UniqueConstraint("project_id", "stage_index", "days_before", name="uq_reminder"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    stage_index: Mapped[int] = mapped_column(Integer)
    days_before: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[date] = mapped_column(Date)
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


def ensure_stage_rows(project: Project) -> None:
    """Гарантирует наличие строк для всех 29 этапов. / Ensure all 29 stage rows exist."""
    existing = {s.stage_index for s in project.stages}
    for s in STAGES:
        if s.index not in existing:
            project.stages.append(ProjectStage(stage_index=s.index))

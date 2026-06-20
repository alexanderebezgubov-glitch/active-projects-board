"""Планировщик автопингов о приближающихся дедлайнах.

Scheduler for automatic deadline-reminder pings.

Каждый день в заданное время проверяем все проекты. Для каждого проекта берём
его ближайший дедлайн (плановую дату текущего/ближайшего незавершённого этапа).
Если до него осталось ровно N дней (N из REMINDER_DAYS_BEFORE) или он просрочен
и пинг ещё не отправлялся — рассылаем уведомление всем пользователям по их
каналам (Telegram + email). ReminderLog защищает от повторов.
"""
from __future__ import annotations

import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from . import config
from .db import SessionLocal
from .i18n import t
from .models import Project, ReminderLog, User
from .notifications import send_email, send_telegram
from .stages import stage_name

log = logging.getLogger("scheduler")


def _format_message(project: Project, deadline: date, stage_index: int,
                    days_left: int, lang: str) -> tuple[str, str]:
    stage = stage_name(stage_index, lang)
    if days_left < 0:
        when = f"{t('overdue', lang)} ({-days_left})"
    elif days_left == 0:
        when = t("due_today", lang)
    else:
        when = f"{days_left} {t('days_left', lang)}"
    if lang == "en":
        body = (f"Project: {project.name}\n"
                f"Stage: {stage_index}. {stage}\n"
                f"Deadline: {deadline.isoformat()} — {when}")
    else:
        body = (f"Проект: {project.name}\n"
                f"Этап: {stage_index}. {stage}\n"
                f"Дедлайн: {deadline.isoformat()} — {when}")
    subject = f"⏰ {t('reminder_subject', lang)}: {project.name}"
    return subject, body


def check_deadlines(today: date | None = None) -> int:
    """Проверить дедлайны и разослать пинги. Возвращает число отправленных.

    Check deadlines and dispatch pings. Returns the number of messages sent.
    """
    today = today or date.today()
    sent = 0
    with SessionLocal() as db:
        users = list(db.scalars(select(User)))
        projects = list(db.scalars(select(Project)))
        for project in projects:
            deadline = project.next_deadline
            stage_index = project.current_stage_index
            if deadline is None or stage_index is None:
                continue
            days_left = (deadline - today).days

            # Решаем, на какой порог реагируем сегодня.
            trigger_threshold: int | None = None
            if days_left < 0:
                trigger_threshold = -1  # просрочка / overdue bucket
            elif days_left in config.REMINDER_DAYS_BEFORE:
                trigger_threshold = days_left
            if trigger_threshold is None:
                continue

            # Защита от повторной отправки. / Dedup.
            already = db.scalar(
                select(ReminderLog).where(
                    ReminderLog.project_id == project.id,
                    ReminderLog.stage_index == stage_index,
                    ReminderLog.days_before == trigger_threshold,
                    ReminderLog.deadline == deadline,
                )
            )
            if already:
                continue

            for user in users:
                lang = user.lang or "ru"
                subject, body = _format_message(
                    project, deadline, stage_index, days_left, lang)
                if user.telegram_chat_id:
                    if send_telegram(user.telegram_chat_id, f"<b>{subject}</b>\n{body}"):
                        sent += 1
                if user.email:
                    if send_email(user.email, subject, body):
                        sent += 1

            db.add(ReminderLog(
                project_id=project.id,
                stage_index=stage_index,
                days_before=trigger_threshold,
                deadline=deadline,
            ))
            db.commit()
    log.info("Deadline check done, %s messages sent", sent)
    return sent


_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    hour, _, minute = config.DAILY_CHECK_TIME.partition(":")
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(
        check_deadlines,
        CronTrigger(hour=int(hour or 9), minute=int(minute or 0)),
        id="daily_deadline_check",
        replace_existing=True,
    )
    sched.start()
    _scheduler = sched
    log.info("Scheduler started, daily check at %s", config.DAILY_CHECK_TIME)
    return sched

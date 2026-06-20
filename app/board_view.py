"""Расчёт модели представления доски. / Board view-model computation.

Чистые функции, превращающие проекты из БД в данные для шаблона: сводка,
«лента» из 29 этапов, центр напоминаний и готовые тексты сообщений.
Pure functions turning DB projects into template data: summary, the 29-stage
rail, the reminder centre and ready-to-send message texts.
"""

from __future__ import annotations

from datetime import date

from .i18n import t
from .models import Project
from .stages import STAGE_COUNT, stage_name

_MONTHS = {
    "ru": ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def days_left(d: date | None, today: date) -> int | None:
    return None if d is None else (d - today).days


def fmt_date(d: date | None, lang: str) -> str:
    if d is None:
        return "—"
    return f"{d.day:02d} {_MONTHS.get(lang, _MONTHS['en'])[d.month - 1]}"


def left_label(d: date | None, today: date, threshold: int, lang: str) -> dict:
    n = days_left(d, today)
    if n is None:
        return {"txt": t("no_dl", lang), "cls": ""}
    days = t("days", lang)
    if n < 0:
        return {"txt": f"{t('overdue_by', lang)} {abs(n)} {days}", "cls": "c-over"}
    if n == 0:
        return {"txt": t("due_today", lang), "cls": "c-over"}
    cls = "c-soon" if n <= threshold else "c-ok"
    return {"txt": f"{n} {days} {t('left', lang)}", "cls": cls}


def _next_stage_deadline(p: Project) -> tuple[int, date] | None:
    """Ближайший незавершённый этап с датой. / Nearest incomplete dated stage."""
    sm = p.stage_map
    start = p.current_stage_index or STAGE_COUNT
    for i in range(start, STAGE_COUNT + 1):
        row = sm.get(i)
        if row and not row.completed and row.planned_date:
            return i, row.planned_date
    return None


def build_message(p: Project, kind: str, stage_idx: int, d: date, today: date, lang: str) -> str:
    n = days_left(d, today)
    if n is None:
        when = ""
    elif n < 0:
        when = f"просрочено на {abs(n)} дн." if lang == "ru" else f"overdue by {abs(n)} d"
    elif n == 0:
        when = "сегодня" if lang == "ru" else "today"
    else:
        when = f"через {n} дн." if lang == "ru" else f"in {n} d"

    if kind == "final":
        what = t("ping_final", lang)
    else:
        nm = stage_name(stage_idx, lang)
        what = f"{t('ping_stage', lang)} — №{stage_idx}/{STAGE_COUNT} «{nm}»"

    head = f"🔔 {t('reminder_hi', lang)}: {p.name}"
    date_lbl = "Дата" if lang == "ru" else "Date"
    return f"{head}\n{what}\n{date_lbl}: {fmt_date(d, lang)} ({when})"


def rail_cells(p: Project, today: date, threshold: int, lang: str) -> list[dict]:
    sm = p.stage_map
    cur = p.current_stage_index  # 1-based or None
    cells = []
    for i in range(1, STAGE_COUNT + 1):
        row = sm.get(i)
        completed = bool(row and row.completed)
        active = cur is not None and i == cur
        pdate = row.planned_date if row else None
        n = days_left(pdate, today)
        flag = (not completed) and pdate is not None and n is not None and n <= threshold
        cells.append(
            {
                "i": i,
                "state": "done" if completed else ("active" if active else ""),
                "flag": flag,
                "name": stage_name(i, lang),
                "date": fmt_date(pdate, lang) if pdate else "",
                "label": left_label(pdate, today, threshold, lang)["txt"] if pdate else "",
            }
        )
    return cells


def board_rows(projects: list[Project], today: date, threshold: int, lang: str) -> list[dict]:
    rows = []
    for p in projects:
        cur = p.current_stage_index
        ns = _next_stage_deadline(p)
        stage_dl = p.stage_map[cur].planned_date if cur else None
        rows.append(
            {
                "p": p,
                "cur": cur,
                "all_done": cur is None,
                "stage_name": stage_name(cur, lang) if cur else t("all_done", lang),
                "completed": p.completed_count,
                "next_idx": ns[0] if ns else None,
                "next_date": fmt_date(ns[1], lang) if ns else "—",
                "stage_label": left_label(stage_dl, today, threshold, lang),
                "stage_dl_iso": stage_dl.isoformat() if stage_dl else "",
                "final_iso": p.final_deadline.isoformat() if p.final_deadline else "",
                "final_date": fmt_date(p.final_deadline, lang),
                "final_label": left_label(p.final_deadline, today, threshold, lang),
                "cells": rail_cells(p, today, threshold, lang),
            }
        )
    # просроченные и срочные — наверх / overdue and urgent first
    rows.sort(key=lambda r: _row_worst(r["p"], today))
    return rows


def _row_worst(p: Project, today: date) -> float:
    cand = []
    ns = _next_stage_deadline(p)
    if ns:
        cand.append(days_left(ns[1], today))
    if p.final_deadline:
        cand.append(days_left(p.final_deadline, today))
    cand = [c for c in cand if c is not None]
    return min(cand) if cand else float("inf")


def summary(projects: list[Project], today: date, threshold: int) -> dict:
    soon = over = 0
    for p in projects:
        worst = _row_worst(p, today)
        if worst < 0:
            over += 1
        elif worst <= threshold:
            soon += 1
    return {"active": len(projects), "soon": soon, "over": over}


def reminder_rows(projects: list[Project], today: date, threshold: int, lang: str) -> list[dict]:
    rows = []
    for p in projects:
        cur = p.current_stage_index
        if cur:
            sd = p.stage_map[cur].planned_date
            n = days_left(sd, today)
            if n is not None and n <= threshold:
                rows.append(_reminder(p, "stage", cur, sd, n, today, lang))
        n = days_left(p.final_deadline, today)
        if n is not None and n <= threshold:
            rows.append(_reminder(p, "final", cur or STAGE_COUNT, p.final_deadline, n, today, lang))
    rows.sort(key=lambda r: r["n"])
    return rows


def _reminder(p, kind, stage_idx, d, n, today, lang) -> dict:
    if n < 0:
        when = f"{t('overdue_by', lang)} {abs(n)}{'дн.' if lang == 'ru' else 'd'}"
    elif n == 0:
        when = t("due_today", lang)
    else:
        when = f"{n}{' дн.' if lang == 'ru' else 'd'}"
    return {
        "p": p,
        "n": n,
        "when": when,
        "when_cls": "w-over" if n < 0 else "w-soon",
        "icon": "✈️" if p.channel == "telegram" else "🟢",
        "message": build_message(p, kind, stage_idx, d, today, lang),
    }

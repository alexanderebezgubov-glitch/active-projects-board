"""Детекция дедлайнов и дедупликация пингов. / Deadline detection and ping dedup."""
from datetime import date, timedelta

from app.models import Project, ReminderLog, ensure_stage_rows
from app.scheduler import check_deadlines


def _project_with_deadline(db, name, stage_index, deadline):
    p = Project(name=name)
    ensure_stage_rows(p)
    for i in range(1, stage_index):
        p.stage_map[i].completed = True
    p.stage_map[stage_index].planned_date = deadline
    db.add(p)
    db.commit()
    return p


def test_overdue_and_threshold_logged_once(db):
    today = date(2026, 6, 20)
    _project_with_deadline(db, "Overdue", 10, today - timedelta(days=1))
    _project_with_deadline(db, "In3Days", 6, today + timedelta(days=3))   # порог 3 / threshold
    _project_with_deadline(db, "In5Days", 6, today + timedelta(days=5))   # не порог / no threshold

    check_deadlines(today=today)
    logs = db.query(ReminderLog).all()
    triggered = {db.get(Project, row.project_id).name: row.days_before for row in logs}
    assert triggered == {"Overdue": -1, "In3Days": 3}

    # повторный прогон не плодит записи / second run does not duplicate
    check_deadlines(today=today)
    assert db.query(ReminderLog).count() == 2

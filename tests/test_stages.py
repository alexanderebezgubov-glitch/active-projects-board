"""Этапы и производные свойства проекта. / Stages and derived project properties."""
from datetime import date

from app.models import Project, ensure_stage_rows
from app.stages import STAGE_COUNT, STAGES, stage_name


def test_catalog_has_29_sequential_stages():
    assert STAGE_COUNT == 29
    assert [s.index for s in STAGES] == list(range(1, 30))
    assert all(s.ru and s.en for s in STAGES)


def test_stage_name_localized():
    assert stage_name(1, "ru") == "Инспекция"
    assert stage_name(1, "en") == "Inspection"
    assert stage_name(999, "ru") == "#999"


def test_current_stage_is_first_incomplete(db):
    p = Project(name="P")
    ensure_stage_rows(p)
    db.add(p)
    db.commit()
    assert p.current_stage_index == 1  # ничего не сделано / nothing done

    sm = p.stage_map
    sm[1].completed = True
    sm[2].completed = True
    db.commit()
    assert p.current_stage_index == 3
    assert p.completed_count == 2


def test_next_deadline_skips_completed_and_undated(db):
    p = Project(name="P")
    ensure_stage_rows(p)
    sm = p.stage_map
    sm[1].completed = True
    sm[1].planned_date = date(2026, 1, 1)   # выполнен — игнор / done, ignored
    sm[2].planned_date = None               # без даты — пропуск / no date, skipped
    sm[3].planned_date = date(2026, 6, 25)  # ближайший актуальный / nearest active
    db.add(p)
    db.commit()
    assert p.current_stage_index == 2
    assert p.next_deadline == date(2026, 6, 25)


def test_all_done_has_no_current_stage(db):
    p = Project(name="P")
    ensure_stage_rows(p)
    for row in p.stages:
        row.completed = True
    db.add(p)
    db.commit()
    assert p.current_stage_index is None
    assert p.next_deadline is None

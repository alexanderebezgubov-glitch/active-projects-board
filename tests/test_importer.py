"""Импорт CSV/Excel. / CSV-Excel import."""
import datetime
import io

from app.importer import TEMPLATE_CSV, apply_rows, parse_upload
from app.models import Project


def test_csv_semicolon_russian_headers_and_dates(db):
    raw = ("проект;этап;дата;выполнено\n"
           "Офис А;5;20.06.2026;да\n"
           "Офис А;6;25.06.2026;нет\n"
           "Кафе Б;14;2026-07-02;\n").encode()
    rows = parse_upload("data.csv", raw)
    result = apply_rows(db, rows)

    assert result["applied"] == 3
    assert sorted(result["created"]) == ["Кафе Б", "Офис А"]
    assert result["errors"] == []

    ofis = db.query(Project).filter_by(name="Офис А").first()
    sm = ofis.stage_map
    assert sm[5].completed is True
    assert sm[5].planned_date == datetime.date(2026, 6, 20)
    assert sm[6].completed is False
    assert sm[6].planned_date == datetime.date(2026, 6, 25)


def test_xlsx_with_real_date_cell(db):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["project", "stage", "planned_date", "completed"])
    ws.append(["Showroom", 10, datetime.date(2026, 8, 1), "yes"])
    buf = io.BytesIO()
    wb.save(buf)

    rows = parse_upload("data.xlsx", buf.getvalue())
    result = apply_rows(db, rows)
    assert result["applied"] == 1
    p = db.query(Project).filter_by(name="Showroom").first()
    assert p.stage_map[10].planned_date == datetime.date(2026, 8, 1)
    assert p.stage_map[10].completed is True


def test_existing_project_is_updated_not_duplicated(db):
    raw1 = b"project,stage,planned_date\nA,3,2026-06-10\n"
    raw2 = b"project,stage,planned_date\nA,4,2026-06-20\n"
    apply_rows(db, parse_upload("a.csv", raw1))
    result = apply_rows(db, parse_upload("a.csv", raw2))

    assert db.query(Project).filter_by(name="A").count() == 1
    assert result["created"] == []
    assert result["updated"] == ["A"]


def test_bad_rows_collected_others_applied(db):
    raw = b"project,stage,planned_date\nX,99,2026-01-01\nX,abc,2026-01-01\nX,5,2026-01-01\n"
    result = apply_rows(db, parse_upload("b.csv", raw))
    assert result["applied"] == 1
    assert len(result["errors"]) == 2


def test_template_parses(db):
    rows = parse_upload("t.csv", TEMPLATE_CSV.encode("utf-8-sig"))
    assert len(rows) == 3
    assert all("project" in r and "stage" in r for r in rows)

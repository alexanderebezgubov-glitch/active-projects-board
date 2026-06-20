"""Демо-данные для проверки доски. / Demo data to try the board.

Запуск: python seed.py   (создаёт пару проектов и пользователя admin/admin)
Run:    python seed.py   (creates a couple of projects and admin/admin user)
"""

from datetime import date, timedelta

from app.auth import hash_password
from app.db import SessionLocal, init_db
from app.models import Project, User, ensure_stage_rows


def run() -> None:
    init_db()
    today = date.today()
    with SessionLocal() as db:
        if db.query(User).count() == 0:
            db.add(
                User(
                    username="admin", password_hash=hash_password("admin"), lang="ru", is_admin=True
                )
            )

        if db.query(Project).count() == 0:
            demo = [
                ("Офис А / Office A", 6, today + timedelta(days=2)),
                ("Кафе Б / Cafe B", 14, today + timedelta(days=9)),
                ("Шоурум В / Showroom C", 10, today - timedelta(days=1)),
            ]
            for name, current, deadline in demo:
                p = Project(name=name)
                ensure_stage_rows(p)
                sm = {s.stage_index: s for s in p.stages}
                # пометить пройденные этапы выполненными / mark prior stages done
                for i in range(1, current):
                    sm[i].completed = True
                # дедлайн текущего этапа / deadline of the current stage
                sm[current].planned_date = deadline
                db.add(p)
        db.commit()
    print("Seed done. Login: admin / admin")


if __name__ == "__main__":
    run()

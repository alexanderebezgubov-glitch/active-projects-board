"""Демо-данные для проверки доски. / Demo data to try the board.

Запуск: python seed.py   (создаёт пользователя admin/admin и пару объектов)
Run:    python seed.py   (creates the admin/admin user and a few projects)
"""

from datetime import date, timedelta

from app.auth import hash_password
from app.db import SessionLocal, init_db
from app.models import Project, User, ensure_stage_rows


def run() -> None:
    init_db()
    today = date.today()

    def d(off: int) -> date:
        return today + timedelta(days=off)

    # name, current_stage(1-based), final, channel, contact, {stage_index: date}
    demo = [
        ("Office 1204, JLT", 10, d(34), "telegram", "@pm_alex", {10: d(2), 13: d(11), 19: d(20)}),
        ("Clinic, Business Bay", 4, d(58), "whatsapp", "+9715xxxxxxx", {4: d(-1), 7: d(9)}),
        ("Showroom, Sheikh Zayed Rd", 23, d(6), "telegram", "@site_lead", {23: d(4)}),
    ]

    with SessionLocal() as db:
        if db.query(User).count() == 0:
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password("admin"),
                    lang="ru",
                    is_admin=True,
                )
            )

        if db.query(Project).count() == 0:
            for name, cur, final, channel, contact, deadlines in demo:
                p = Project(name=name, final_deadline=final, channel=channel, contact=contact)
                ensure_stage_rows(p)
                sm = {s.stage_index: s for s in p.stages}
                for i in range(1, cur):  # пройденные этапы / completed stages
                    sm[i].completed = True
                for idx, dl in deadlines.items():
                    sm[idx].planned_date = dl
                db.add(p)
        db.commit()
    print("Seed done. Login: admin / admin")


if __name__ == "__main__":
    run()

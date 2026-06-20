"""FastAPI-приложение: маршруты, шаблоны, запуск. / FastAPI app: routes, templates."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from . import board_view, config
from .auth import authenticate, current_user, hash_password
from .db import get_session, init_db
from .i18n import normalize_lang, t
from .importer import TEMPLATE_CSV, ImportError_, apply_rows, parse_upload
from .models import Project, ProjectStage, User, ensure_stage_rows
from .scheduler import check_deadlines, start_scheduler
from .stages import STAGE_COUNT, STAGES, stage_name

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Active Projects Board")
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, max_age=60 * 60 * 24 * 14)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
def _startup() -> None:
    init_db()
    _seed_admin()
    start_scheduler()


def _seed_admin() -> None:
    """Создать админа по умолчанию, если пользователей нет. / Seed default admin."""
    from .db import SessionLocal

    with SessionLocal() as db:
        if db.scalar(select(User).limit(1)) is None:
            db.add(
                User(
                    username="admin",
                    password_hash=hash_password("admin"),
                    lang="ru",
                    is_admin=True,
                )
            )
            db.commit()


# --- Хелперы / helpers ---


def get_lang(request: Request, user: User | None) -> str:
    lang = request.session.get("lang")
    if lang:
        return normalize_lang(lang)
    if user and user.lang:
        return normalize_lang(user.lang)
    return config.DEFAULT_LANG


def render(request: Request, name: str, lang: str, user: User | None, **ctx) -> HTMLResponse:
    base = {
        "request": request,
        "lang": lang,
        "user": user,
        "t": lambda key: t(key, lang),
        "STAGES": STAGES,
        "STAGE_COUNT": STAGE_COUNT,
        "stage_name": lambda i: stage_name(i, lang),
        "today": date.today(),
    }
    base.update(ctx)
    return templates.TemplateResponse(name, base)


def require_user(request: Request, db: Session) -> User | RedirectResponse:
    user = current_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return user


# --- Аутентификация / auth routes ---


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, db: Session = Depends(get_session)):
    user = current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=303)
    lang = get_lang(request, None)
    return render(request, "login.html", lang, None, error=None)


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session),
):
    user = authenticate(db, username, password)
    lang = get_lang(request, None)
    if not user:
        return render(request, "login.html", lang, None, error=t("login_error", lang))
    request.session["user_id"] = user.id
    request.session["lang"] = user.lang
    return RedirectResponse("/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/set-lang/{lang}")
def set_lang(lang: str, request: Request, db: Session = Depends(get_session)):
    lang = normalize_lang(lang)
    request.session["lang"] = lang
    user = current_user(request, db)
    if user:
        user.lang = lang
        db.commit()
    ref = request.headers.get("referer", "/")
    return RedirectResponse(ref, status_code=303)


# --- Доска / board ---


def get_threshold(request: Request) -> int:
    try:
        return max(1, min(60, int(request.session.get("threshold", 3))))
    except (TypeError, ValueError):
        return 3


@app.get("/", response_class=HTMLResponse)
def board(request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    lang = get_lang(request, user)
    threshold = get_threshold(request)
    today = date.today()
    projects = list(db.scalars(select(Project).order_by(Project.name)))
    return render(
        request,
        "board.html",
        lang,
        user,
        rows=board_view.board_rows(projects, today, threshold, lang),
        reminders=board_view.reminder_rows(projects, today, threshold, lang),
        summary=board_view.summary(projects, today, threshold),
        threshold=threshold,
    )


@app.post("/set-threshold")
def set_threshold(request: Request, threshold: int = Form(3), db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    request.session["threshold"] = max(1, min(60, threshold))
    return RedirectResponse("/", status_code=303)


# --- Проекты / projects ---


@app.post("/projects/new")
def create_project(request: Request, name: str = Form(...), db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    name = name.strip()
    if name:
        project = Project(name=name)
        ensure_stage_rows(project)
        db.add(project)
        db.commit()
        return RedirectResponse(f"/projects/{project.id}", status_code=303)
    return RedirectResponse("/", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail(project_id: int, request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    lang = get_lang(request, user)
    project = db.get(Project, project_id)
    if not project:
        return RedirectResponse("/", status_code=303)
    ensure_stage_rows(project)
    db.commit()
    return render(request, "project.html", lang, user, project=project, stage_map=project.stage_map)


@app.post("/projects/{project_id}")
async def update_project(project_id: int, request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    project = db.get(Project, project_id)
    if not project:
        return RedirectResponse("/", status_code=303)
    form = await request.form()
    name = (form.get("name") or "").strip()
    if name:
        project.name = name
    ensure_stage_rows(project)
    sm = project.stage_map
    for s in STAGES:
        row: ProjectStage = sm[s.index]
        raw_date = (form.get(f"date_{s.index}") or "").strip()
        row.planned_date = _parse_date(raw_date)
        completed = form.get(f"done_{s.index}") is not None
        if completed and not row.completed:
            row.completed = True
            row.completed_at = datetime.utcnow()
        elif not completed and row.completed:
            row.completed = False
            row.completed_at = None
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/projects/{project_id}/delete")
def delete_project(project_id: int, request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    project = db.get(Project, project_id)
    if project:
        db.delete(project)
        db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/save-project")
def save_project(
    request: Request,
    id: str = Form(""),
    name: str = Form(...),
    final: str = Form(""),
    channel: str = Form("telegram"),
    contact: str = Form(""),
    db: Session = Depends(get_session),
):
    """Создать или обновить мета-данные проекта (из модалки). / Create or edit project meta."""
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    name = name.strip()
    if not name:
        return RedirectResponse("/", status_code=303)
    channel = channel if channel in ("telegram", "whatsapp") else "telegram"
    project = db.get(Project, int(id)) if id.strip().isdigit() else None
    if project is None:
        project = Project(name=name)
        ensure_stage_rows(project)
        db.add(project)
    project.name = name
    project.final_deadline = _parse_date(final.strip())
    project.channel = channel
    project.contact = contact.strip() or None
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/projects/{project_id}/advance")
def advance_stage(project_id: int, request: Request, db: Session = Depends(get_session)):
    """Отметить текущий этап выполненным. / Mark the current stage done."""
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    project = db.get(Project, project_id)
    if project:
        idx = project.current_stage_index
        if idx is not None:
            row = project.stage_map[idx]
            row.completed = True
            row.completed_at = datetime.utcnow()
            db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/projects/{project_id}/back")
def back_stage(project_id: int, request: Request, db: Session = Depends(get_session)):
    """Вернуть последний завершённый этап в работу. / Reopen the last completed stage."""
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    project = db.get(Project, project_id)
    if project:
        done = [s for s in project.stages if s.completed]
        if done:
            row = max(done, key=lambda s: s.stage_index)
            row.completed = False
            row.completed_at = None
            db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/projects/{project_id}/stage-deadline")
def set_stage_deadline(
    project_id: int, request: Request, date: str = Form(""), db: Session = Depends(get_session)
):
    """Дедлайн текущего этапа. / Planned date of the current stage."""
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    project = db.get(Project, project_id)
    if project:
        idx = project.current_stage_index
        if idx is not None:
            project.stage_map[idx].planned_date = _parse_date(date.strip())
            db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/projects/{project_id}/final-deadline")
def set_final_deadline(
    project_id: int, request: Request, date: str = Form(""), db: Session = Depends(get_session)
):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    project = db.get(Project, project_id)
    if project:
        project.final_deadline = _parse_date(date.strip())
        db.commit()
    return RedirectResponse("/", status_code=303)


# --- Импорт CSV/Excel / CSV-Excel import ---


@app.get("/import", response_class=HTMLResponse)
def import_form(request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    lang = get_lang(request, user)
    return render(request, "import.html", lang, user, result=None, error=None)


@app.get("/import/template.csv")
def import_template(request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    return Response(
        content=TEMPLATE_CSV.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=projects_template.csv"},
    )


@app.post("/import", response_class=HTMLResponse)
async def import_run(
    request: Request, file: UploadFile = File(...), db: Session = Depends(get_session)
):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    lang = get_lang(request, user)
    content = await file.read()
    try:
        rows = parse_upload(file.filename or "", content)
        result = apply_rows(db, rows)
    except ImportError_ as exc:
        return render(request, "import.html", lang, user, result=None, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        return render(
            request, "import.html", lang, user, result=None, error=f"{type(exc).__name__}: {exc}"
        )
    return render(request, "import.html", lang, user, result=result, error=None)


# --- Настройки пользователя / user settings ---


@app.get("/settings", response_class=HTMLResponse)
def settings_form(request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    lang = get_lang(request, user)
    return render(request, "settings.html", lang, user, saved=False)


@app.post("/settings")
def settings_save(
    request: Request,
    email: str = Form(""),
    telegram_chat_id: str = Form(""),
    lang_pref: str = Form("ru"),
    db: Session = Depends(get_session),
):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    user.email = email.strip() or None
    user.telegram_chat_id = telegram_chat_id.strip() or None
    user.lang = normalize_lang(lang_pref)
    db.commit()
    request.session["lang"] = user.lang
    return render(request, "settings.html", user.lang, user, saved=True)


# --- Ручной запуск проверки (для отладки) / manual check trigger ---


@app.post("/admin/run-check")
def run_check(request: Request, db: Session = Depends(get_session)):
    user = require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    sent = check_deadlines()
    return {"sent": sent}


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None

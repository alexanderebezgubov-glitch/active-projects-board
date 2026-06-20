"""Простая двуязычность интерфейса (RU/EN). / Simple UI i18n (RU/EN)."""

LANGS = ("ru", "en")

TRANSLATIONS: dict[str, dict[str, str]] = {
    "app_title": {"ru": "Доска активных объектов", "en": "Active Projects Board"},
    "board": {"ru": "Доска", "en": "Board"},
    "projects": {"ru": "Проекты", "en": "Projects"},
    "project": {"ru": "Проект", "en": "Project"},
    "current_stage": {"ru": "Текущий этап", "en": "Current stage"},
    "next_deadline": {"ru": "Следующий дедлайн", "en": "Next deadline"},
    "progress": {"ru": "Прогресс", "en": "Progress"},
    "status": {"ru": "Статус", "en": "Status"},
    "actions": {"ru": "Действия", "en": "Actions"},
    "add_project": {"ru": "Добавить проект", "en": "Add project"},
    "edit": {"ru": "Редактировать", "en": "Edit"},
    "save": {"ru": "Сохранить", "en": "Save"},
    "cancel": {"ru": "Отмена", "en": "Cancel"},
    "delete": {"ru": "Удалить", "en": "Delete"},
    "name": {"ru": "Название", "en": "Name"},
    "stage": {"ru": "Этап", "en": "Stage"},
    "planned_date": {"ru": "Плановая дата", "en": "Planned date"},
    "completed": {"ru": "Выполнено", "en": "Completed"},
    "done": {"ru": "Готово", "en": "Done"},
    "no_deadline": {"ru": "—", "en": "—"},
    "no_projects": {
        "ru": "Пока нет проектов. Добавьте первый.",
        "en": "No projects yet. Add the first one.",
    },
    "all_done": {"ru": "Все этапы завершены", "en": "All stages completed"},
    "overdue": {"ru": "Просрочено", "en": "Overdue"},
    "due_today": {"ru": "Сегодня", "en": "Today"},
    "days_left": {"ru": "ост. дней", "en": "days left"},
    "login": {"ru": "Войти", "en": "Sign in"},
    "logout": {"ru": "Выйти", "en": "Sign out"},
    "username": {"ru": "Логин", "en": "Username"},
    "password": {"ru": "Пароль", "en": "Password"},
    "login_error": {"ru": "Неверный логин или пароль", "en": "Invalid username or password"},
    "settings": {"ru": "Настройки", "en": "Settings"},
    "notifications": {"ru": "Уведомления", "en": "Notifications"},
    "telegram_chat_id": {"ru": "Telegram chat ID", "en": "Telegram chat ID"},
    "email": {"ru": "Email", "en": "Email"},
    "language": {"ru": "Язык", "en": "Language"},
    "stages_of": {"ru": "Этапы проекта", "en": "Project stages"},
    "back_to_board": {"ru": "← К доске", "en": "← Back to board"},
    "reminder_subject": {"ru": "Напоминание о дедлайне", "en": "Deadline reminder"},
    "telegram_help": {
        "ru": "Чтобы получать пинги: напишите боту в Telegram, затем впишите сюда ваш chat ID "
        "(узнать можно через @userinfobot).",
        "en": "To receive pings: message the bot in Telegram, then enter your chat ID here "
        "(get it from @userinfobot).",
    },
    "save_settings": {"ru": "Сохранить настройки", "en": "Save settings"},
    "mark_done": {"ru": "Отметить выполненным", "en": "Mark done"},
    "reopen": {"ru": "Вернуть в работу", "en": "Reopen"},
    "confirm_delete": {"ru": "Удалить проект?", "en": "Delete this project?"},
    "import": {"ru": "Импорт", "en": "Import"},
    "import_data": {"ru": "Импорт из CSV / Excel", "en": "Import from CSV / Excel"},
    "upload_file": {"ru": "Файл (CSV или .xlsx)", "en": "File (CSV or .xlsx)"},
    "run_import": {"ru": "Загрузить", "en": "Upload"},
    "download_template": {"ru": "Скачать шаблон CSV", "en": "Download CSV template"},
    "import_help": {
        "ru": "Таблица с колонками: project (название), stage (№ этапа 1–29), "
        "planned_date (ГГГГ-ММ-ДД), completed (да/нет — необязательно). "
        "Одна строка = один дедлайн этапа. Проекты создаются автоматически, "
        "существующие — обновляются по названию.",
        "en": "A table with columns: project (name), stage (stage no. 1–29), "
        "planned_date (YYYY-MM-DD), completed (yes/no — optional). "
        "One row = one stage deadline. Projects are created automatically; "
        "existing ones are matched by name and updated.",
    },
    "import_done": {"ru": "Импорт завершён", "en": "Import finished"},
    "rows_applied": {"ru": "Строк применено", "en": "Rows applied"},
    "projects_created": {"ru": "Создано проектов", "en": "Projects created"},
    "projects_updated": {"ru": "Обновлено проектов", "en": "Projects updated"},
    "errors": {"ru": "Ошибки", "en": "Errors"},
    # --- редизайн «BuildBoard» / "BuildBoard" redesign ---
    "brand": {"ru": "СтройБорд", "en": "BuildBoard"},
    "brand_sub": {"ru": "ОБЪЕКТЫ", "en": "FIT-OUT"},
    "active": {"ru": "Активные", "en": "Active"},
    "due_soon": {"ru": "Скоро дедлайн", "en": "Due soon"},
    "reminder_centre": {"ru": "Центр напоминаний", "en": "Reminder centre"},
    "threshold_lbl": {"ru": "Порог", "en": "Window"},
    "days": {"ru": "дн.", "en": "d"},
    "left": {"ru": "осталось", "en": "left"},
    "overdue_by": {"ru": "просрочка", "en": "overdue"},
    "no_dl": {"ru": "не задан", "en": "not set"},
    "next_dl": {"ru": "След. дедлайн", "en": "Next deadline"},
    "final": {"ru": "Сдача", "en": "Handover"},
    "advance": {"ru": "Этап выполнен →", "en": "Stage done →"},
    "back": {"ru": "← Назад", "en": "← Back"},
    "stage_deadline": {"ru": "Дедлайн этапа", "en": "Stage deadline"},
    "empty_ping": {
        "ru": "Нет приближающихся дедлайнов в пределах порога. Всё под контролем.",
        "en": "No deadlines within the window. All clear.",
    },
    "ping_stage": {"ru": "Дедлайн этапа", "en": "Stage deadline"},
    "ping_final": {"ru": "Дедлайн сдачи объекта", "en": "Project handover deadline"},
    "reminder_hi": {"ru": "Напоминание", "en": "Reminder"},
    "new_project": {"ru": "Новый проект", "en": "New project"},
    "edit_project": {"ru": "Редактировать проект", "en": "Edit project"},
    "proj_name": {"ru": "Название проекта", "en": "Project name"},
    "final_dl": {"ru": "Финальный дедлайн (сдача)", "en": "Final deadline (handover)"},
    "channel": {"ru": "Канал напоминаний", "en": "Reminder channel"},
    "contact": {"ru": "Получатель (@username / телефон)", "en": "Recipient (@username / phone)"},
    "open_stages": {"ru": "Все этапы", "en": "All stages"},
    "deadline_note": {
        "ru": "Реальная отправка пингов в Telegram/WhatsApp выполняется серверным ботом "
        "по расписанию (см. README). Тексты ниже — то, что уйдёт в мессенджер.",
        "en": "Actual Telegram/WhatsApp delivery is handled by the scheduled server bot "
        "(see README). The texts below are exactly what gets sent.",
    },
}


def t(key: str, lang: str) -> str:
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang) or entry.get("ru") or key


def normalize_lang(lang: str | None) -> str:
    return lang if lang in LANGS else "ru"

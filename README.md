# Доска активных объектов / Active Projects Board

[![CI](https://github.com/alexanderebezgubov-glitch/active-projects-board/actions/workflows/ci.yml/badge.svg)](https://github.com/alexanderebezgubov-glitch/active-projects-board/actions/workflows/ci.yml)

Веб-приложение для отслеживания строительных/отделочных проектов: на каком из
**29 этапов** находится каждый объект, какой у него **ближайший дедлайн**, плюс
**автопинги** в Telegram и по email о приближающихся сроках. Интерфейс на
**русском и английском**, рассчитан на команду (общий доступ, авторизация).

A web app to track fit-out projects: which of the **29 stages** each site is on,
its **next deadline**, plus **automatic reminders** via Telegram and email.
Bilingual **RU/EN**, multi-user with simple auth.

---

## Возможности / Features

- Доска всех проектов: текущий этап, прогресс (N/29), ближайший дедлайн, статус
  (в срок / скоро / срочно / просрочено).
- Карточка проекта: 29 этапов, плановая дата и отметка «выполнено» по каждому.
  «Текущий этап» = первый невыполненный; «следующий дедлайн» считается автоматически.
- Автопинги: ежедневная проверка; напоминания за `7,3,1` дней (настраивается) и при
  просрочке. Дедупликация — один и тот же пинг не приходит дважды.
- Каналы: Telegram-бот + email (SMTP). WhatsApp — заготовка под Business API.
- RU/EN переключатель, выбор языка сохраняется у пользователя (на нём же приходят пинги).

## Установка / Setup

```bash
cd project-board
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # заполните SECRET_KEY, Telegram, SMTP
python seed.py                # демо-данные + пользователь admin / admin (опционально)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Откройте http://localhost:8000 — логин `admin` / `admin` (смените пароль/создайте
пользователей; пока пользователей нет, при старте создаётся admin/admin).

## Уведомления / Notifications

- **Telegram**: создайте бота через `@BotFather`, впишите токен в `TELEGRAM_BOT_TOKEN`.
  Каждый пользователь в разделе «Настройки» указывает свой `chat ID`
  (узнать — у `@userinfobot`). Сообщения шлются на языке пользователя.
- **Email**: заполните `SMTP_*` в `.env`. Пользователь указывает email в настройках.
- **WhatsApp**: пока заглушка `send_whatsapp()` в `app/notifications.py` — подключается
  позже через WhatsApp Business API (Twilio / 360dialog).

Время и пороги напоминаний — в `.env`: `DAILY_CHECK_TIME`, `REMINDER_DAYS_BEFORE`.
Проверку можно запустить вручную: `POST /admin/run-check`.

## Импорт из CSV/Excel / CSV-Excel import

Раздел **«Импорт»** в шапке: загрузите `.csv` или `.xlsx`. Формат — «длинная»
таблица, одна строка = один дедлайн этапа:

| project | stage | planned_date | completed |
|---------|-------|--------------|-----------|
| Офис А  | 5     | 2026-06-20   | yes       |
| Офис А  | 6     | 2026-06-25   | no        |
| Кафе Б  | 14    | 2026-07-02   |           |

- Заголовки распознаются на RU и EN (`project/проект`, `stage/этап`,
  `planned_date/дата/дедлайн`, `completed/выполнено`).
- Даты: `ГГГГ-ММ-ДД`, `ДД.ММ.ГГГГ`, ячейки-даты Excel. CSV — разделитель `,` или `;`.
- Проекты создаются автоматически; существующие обновляются по названию.
- Кнопка **«Скачать шаблон CSV»** даёт готовую заготовку. Ошибки по строкам
  показываются после загрузки, остальные строки применяются.

Альтернативы: ввод через UI («Добавить проект») или расширение `seed.py`.

## Запуск в Docker / Run with Docker

```bash
cp .env.example .env          # заполнить SECRET_KEY, Telegram, SMTP
docker compose up --build     # http://localhost:8000
```

БД хранится на томе `board_data` (`/data` в контейнере) и переживает пересборку.
Образ запускает **один** воркер uvicorn (планировщик автопингов — в процессе).

## Структура / Layout

```
app/
  main.py           маршруты FastAPI / routes
  models.py         Project, ProjectStage, User, ReminderLog
  stages.py         29 этапов (RU/EN) / the 29 stages
  i18n.py           переводы интерфейса / UI translations
  scheduler.py      ежедневная проверка дедлайнов / daily deadline check
  notifications.py  Telegram + email (+ WhatsApp stub)
  auth.py           вход и пароли / auth
  templates/, static/
seed.py             демо-данные / demo data
```

## Разработка / Development

Как поднять окружение и запустить тесты — в [CONTRIBUTING.md](CONTRIBUTING.md)
(`pip install -r requirements-dev.txt && pytest`).
Setup and running tests are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Заметки по продакшену / Production notes

- SQLite подходит для небольшой команды; для нагрузки/нескольких воркеров —
  переключите `DATABASE_URL` на PostgreSQL.
- Планировщик живёт в процессе приложения — запускайте **один** воркер uvicorn,
  иначе пинги задвоятся (или вынесите планировщик в отдельный процесс).
- Поставьте за HTTPS-прокси (nginx/Caddy) и смените `SECRET_KEY`.

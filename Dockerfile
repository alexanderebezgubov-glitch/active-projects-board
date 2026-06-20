FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Зависимости отдельным слоем для кэширования. / Deps as a cached layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# БД SQLite и .env монтируются как volume (см. compose). / DB & .env via volume.
ENV DATABASE_URL=sqlite:////data/project_board.db
VOLUME ["/data"]

EXPOSE 8000

# Один воркер: планировщик автопингов живёт в процессе приложения.
# Single worker: the reminder scheduler runs in-process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

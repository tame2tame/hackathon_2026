# Базовый образ закреплён по digest: тот же, в котором собран requirements.lock.
FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Шрифт с кириллицей нужен отчётам в PDF: во fpdf2 встроены только латинские.
RUN apt-get update \
    && apt-get install --no-install-recommends -y fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.lock alembic.ini ./
COPY app ./app
COPY scripts ./scripts
COPY migrations ./migrations
COPY mocks ./mocks

# Сначала точные версии из lock-файла, затем сам пакет без повторного разрешения зависимостей.
RUN pip install -r requirements.lock \
    && pip install --no-deps . \
    && pip check \
    && useradd --system --uid 10001 radar
USER radar

EXPOSE 8000
# Миграции идут отдельным сервисом migrate под владельцем схемы: у приложения прав на DDL нет.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Используем оптимизированный образ Python 3.13
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app/

# Устанавливаем uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Устанавливаем переменные для оптимизации установки uv
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app

# Метаданные проекта
COPY ./pyproject.toml ./uv.lock* /app/

# Копируем код приложения
COPY ./app /app/app

# Установка зависимостей и проекта
RUN uv venv && uv sync --no-dev --frozen

# Копируем миграции
COPY ./alembic.ini /app/alembic.ini

# Копируем и делаем исполняемым entrypoint скрипт
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Открываем порт
EXPOSE 8000

# Указываем entrypoint скрипт для запуска контейнера
ENTRYPOINT ["/app/entrypoint.sh"]
# Используем базовый образ Python 3.12
FROM python:3.12

# Устанавливаем рабочую директорию
WORKDIR /app/

# Устанавливаем uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /bin/uv

# Настраиваем PATH для включения виртуального окружения uv
# Устанавливаем переменные для оптимизации установки uv
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app # Устанавливаем PYTHONPATH

# Копируем файлы зависимостей
COPY ./pyproject.toml ./uv.lock* /app/
# requirements.txt копировать НЕ НУЖНО для uv sync

# Устанавливаем зависимости с помощью uv sync
# --system-site-packages может быть полезен, если нужны системные пакеты,
# но обычно не требуется. Убираем --no-cache-dir, uv кэширует по-своему.
RUN uv venv --python 3.10 /app/.venv && \
    uv pip install --upgrade pip && \
    uv sync --no-dev --strict

# Копируем код приложения
COPY ./app /app/app
COPY ./alembic.ini /app/alembic.ini # Копируем alembic.ini

# Копируем и делаем исполняемым entrypoint скрипт
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Создаем символическую ссылку, если она все еще нужна (лучше избегать, если возможно)
# RUN ln -s /app /app/backend

# Открываем порт
EXPOSE 8000

# Указываем entrypoint скрипт для запуска контейнера
ENTRYPOINT ["/app/entrypoint.sh"]

# CMD больше не нужен, так как exec uvicorn вызывается в конце entrypoint.sh
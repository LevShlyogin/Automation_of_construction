# Используем базовый образ Python 3.13
FROM python:3.13

# Устанавливаем рабочую директорию
WORKDIR /app/

# Устанавливаем uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Настраиваем PATH для включения виртуального окружения uv
# Устанавливаем переменные для оптимизации установки uv
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app

# Копируем файлы зависимостей
COPY ./pyproject.toml ./uv.lock* /app/

# Устанавливаем зависимости с помощью uv sync
# Указываем версию Python, соответствующую базовому образу (или просто не указываем, uv сам найдет)
RUN uv venv && \
    uv sync --no-dev

# Копируем код приложения
COPY ./app /app/app
COPY ./alembic.ini /app/alembic.ini

# Копируем и делаем исполняемым entrypoint скрипт
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Открываем порт
EXPOSE 8000

# Указываем entrypoint скрипт для запуска контейнера
ENTRYPOINT ["/app/entrypoint.sh"]
FROM python:3.10

WORKDIR /app/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.4.15 /uv /bin/uv

ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app

# Сначала копируем только необходимые файлы для зависимостей
COPY ./pyproject.toml ./uv.lock ./requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Затем копируем код приложения в правильную директорию
COPY ./app /app/app
COPY ./alembic.ini /app/

# Добавьте эту строку, если ваш код пытается импортировать из 'backend'
RUN ln -s /app /app/backend

# Пропускаем шаг uv sync, который вызывает ошибку
# RUN --mount=type=cache,target=/root/.cache/uv uv sync

EXPOSE 8000

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
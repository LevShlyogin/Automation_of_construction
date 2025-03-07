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

# Устанавливаем зависимости и явно устанавливаем fastapi[standard]
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install "fastapi[standard]>=0.114.2,<1.0.0"

# Затем копируем код приложения в правильную директорию
COPY ./app /app/app
COPY ./alembic.ini /app/

# Добавьте эту строку, если ваш код пытается импортировать из 'backend'
RUN ln -s /app /app/backend

EXPOSE 8000

# Вместо fastapi CLI используйте uvicorn напрямую
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
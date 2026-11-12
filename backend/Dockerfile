FROM python:3.12-slim

WORKDIR /app

COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --no-deps .

COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000
# Not part of the M1 topology: this image has no E5/Torch, so search and answering cannot run.
# Run migrations as a separate step (alembic upgrade head) before starting the API.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

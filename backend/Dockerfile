FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    libglib2.0-0 libgomp1 \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libfontconfig1 libice6 \
 && rm -rf /var/lib/apt/lists/* \
 || (apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    libglib2.0-0 libgomp1 \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libfontconfig1 libice6 \
 && rm -rf /var/lib/apt/lists/*)

WORKDIR /app

# Copy project metadata, source, and alembic files before editable install
COPY pyproject.toml /app/pyproject.toml
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY src /app/src
COPY models /app/models

# Now editable install works (src already present)
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
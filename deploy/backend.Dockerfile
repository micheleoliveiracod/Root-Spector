FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY root_cause_agent/ ./root_cause_agent/
COPY backend/ ./backend/
COPY config/ ./config/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

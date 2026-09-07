FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY profiler.py demo.py ./
COPY backend/ ./backend/
COPY frontend/ ./frontend/

ENV DATABASE_URL=sqlite:////app/perf_profiler.db

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

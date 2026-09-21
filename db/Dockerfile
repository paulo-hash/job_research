FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data /app/.cache && chmod +x /app/db/entrypoint.sh

ENV JOBS_DB=/app/data/jobs.db
ENV PYTHONUNBUFFERED=1

VOLUME ["/app/data"]

ENTRYPOINT ["/app/db/entrypoint.sh"]
CMD ["python", "main.py"]

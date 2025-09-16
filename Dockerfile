# Dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

ENV PYTHONPATH=/app

CMD ["python", "-m", "bot.main"]
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 app \
    && mkdir -p /app/data \
    && chown app:app /app/data

COPY pipeline/ ./pipeline/
COPY tests/ ./tests/
COPY pytest.ini ./pytest.ini

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

USER app

EXPOSE 8501

CMD ["python", "-m", "pipeline.simulator"]
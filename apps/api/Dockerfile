FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace/apps/api

COPY apps/api /workspace/apps/api
RUN pip install --upgrade pip && pip install /workspace/apps/api

COPY data /workspace/data
ENV PYTHONPATH=/workspace/apps/api OPSASSIST_DATA_DIR=/workspace/data OPSASSIST_AUTO_CREATE_SCHEMA=false
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

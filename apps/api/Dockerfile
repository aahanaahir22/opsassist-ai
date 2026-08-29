FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace

COPY apps/api /workspace/apps/api
RUN pip install --upgrade pip && pip install /workspace/apps/api

COPY data /workspace/data
ENV PYTHONPATH=/workspace/apps/api OPSASSIST_DATA_DIR=/workspace/data
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"
CMD ["uvicorn", "app.main:app", "--app-dir", "/workspace/apps/api", "--host", "0.0.0.0", "--port", "8000"]

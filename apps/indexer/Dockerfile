FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /workspace
COPY apps/api /workspace/apps/api
RUN pip install --upgrade pip && pip install '/workspace/apps/api[semantic]'
COPY data /workspace/data
ENV PYTHONPATH=/workspace/apps/api OPSASSIST_DATA_DIR=/workspace/data OPSASSIST_INDEX_DIR=/indexes OPSASSIST_EMBEDDING_BACKEND=sentence_transformer
VOLUME ["/indexes"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"
CMD ["uvicorn", "app.indexer_main:app", "--app-dir", "/workspace/apps/api", "--host", "0.0.0.0", "--port", "8080"]

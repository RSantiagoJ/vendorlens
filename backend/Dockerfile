FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model so cold starts don't pay download time
RUN python -c "from llama_index.embeddings.fastembed import FastEmbedEmbedding; \
    FastEmbedEmbedding(model_name='BAAI/bge-small-en-v1.5')"

COPY . .

CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}

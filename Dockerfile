FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model into the image so workers never need network
# access to the HuggingFace Hub at runtime (required for nodes without DNS/overlay).
ENV HF_HOME=/models
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Force offline mode at runtime: load the cached model, no HF Hub HEAD requests.
ENV HF_HUB_OFFLINE=1

COPY scripts/worker.py .

CMD ["python", "-u", "worker.py"]

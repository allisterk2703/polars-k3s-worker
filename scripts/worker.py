import logging
import os
import sys

import numpy as np
import polars as pl
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://192.168.0.31:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

STORAGE_OPTIONS = {
    "aws_access_key_id": MINIO_ACCESS_KEY,
    "aws_secret_access_key": MINIO_SECRET_KEY,
    "aws_endpoint_url": MINIO_ENDPOINT,
    "aws_allow_http": "true",
    "aws_s3_allow_unsafe_ssl": "true",
    "force_path_style": "true",
}


def main() -> None:
    # Global partition index = per-Job completion index + an offset, so several
    # Jobs (one per node) can share the same dataset without index collisions.
    offset = int(os.getenv("INDEX_OFFSET", "0"))
    worker_id = offset + int(os.getenv("JOB_COMPLETION_INDEX", "0"))
    input_path = f"s3://datasets/data_part_{worker_id}.parquet"
    output_path = f"s3://datasets/data_processed_{worker_id}.parquet"

    logging.info(f"[Worker {worker_id}] Starting — reading from {input_path}")

    try:
        lazy_df = pl.scan_parquet(input_path, storage_options=STORAGE_OPTIONS)
        processed_lazy = lazy_df.with_columns([
            pl.col("article")
            .str.to_lowercase()
            .str.replace_all(r"[^\w\s]", "")
            .str.strip_chars()
            .alias("cleaned_text")
        ])
        df = processed_lazy.collect()
        df = df.filter(pl.col("cleaned_text").is_not_null() & (pl.col("cleaned_text") != ""))
        logging.info(f"[Worker {worker_id}] Text cleaning done — {len(df)} rows")
    except Exception as e:
        logging.error(f"[Worker {worker_id}] Failed to read or clean data: {e}")
        sys.exit(1)

    logging.info(f"[Worker {worker_id}] Loading SentenceTransformer model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    logging.info(f"[Worker {worker_id}] Generating embeddings...")
    # Encode in batches and log explicit progress lines: tqdm's carriage-return
    # progress bar is invisible in container logs (no TTY), so we print instead.
    texts = df["cleaned_text"].to_list()
    total = len(texts)
    batch_size = 1000
    batches = []
    for start in range(0, total, batch_size):
        batches.append(model.encode(texts[start:start + batch_size], show_progress_bar=False))
        done = min(start + batch_size, total)
        logging.info(f"[Worker {worker_id}] {done}/{total} embeddings")
    embeddings_matrix = np.vstack(batches)

    df = df.with_columns([
        pl.Series(
            name="embeddings",
            values=embeddings_matrix.tolist(),
            dtype=pl.List(pl.Float32),
        )
    ])

    logging.info(f"[Worker {worker_id}] Writing output to {output_path}")
    try:
        df.write_parquet(output_path, storage_options=STORAGE_OPTIONS)
        logging.info(f"[Worker {worker_id}] Done.")
    except Exception as e:
        logging.error(f"[Worker {worker_id}] Failed to write output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

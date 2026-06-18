import os

import polars as pl

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

STORAGE_OPTIONS = {
    "aws_access_key_id": MINIO_ACCESS_KEY,
    "aws_secret_access_key": MINIO_SECRET_KEY,
    "aws_endpoint_url": MINIO_ENDPOINT,
    "force_path_style": "true",
}

NUM_SPLITS = 32

df = pl.read_parquet("data/all-the-articles.parquet")
total_rows = len(df)
rows_per_split = total_rows // NUM_SPLITS

for i in range(NUM_SPLITS):
    offset = i * rows_per_split
    length = rows_per_split if i < NUM_SPLITS - 1 else total_rows - offset
    split_df = df.slice(offset, length)
    path = f"s3://datasets/data_part_{i}.parquet"
    split_df.write_parquet(path, storage_options=STORAGE_OPTIONS)
    print(f"Part {i} uploaded ({len(split_df)} rows) -> {path}")

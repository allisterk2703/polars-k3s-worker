# polars-k3s-worker

Distributed text embedding pipeline running on a 2-node k3s cluster (MacBook Pro M1 + Raspberry Pi 5).

The dataset is split into 32 Parquet partitions stored in MinIO. Each Kubernetes Job schedules indexed workers on a specific node: every worker reads its assigned partition, cleans the text with Polars, generates sentence embeddings using `all-MiniLM-L6-v2` (SentenceTransformers), and writes the result back to MinIO as a new Parquet file with an `embeddings` column.

## Architecture

```
MinIO (192.168.0.33:9000)
    └── datasets/
            ├── data_part_0.parquet  ..  data_part_31.parquet   (input)
            └── data_processed_0.parquet  ..  data_processed_31.parquet  (output)

k3s cluster (N nodes)
    └── Job: N completions, parallelism N — one pod per node via topologySpreadConstraints
```

The Job uses `completionMode: Indexed`. Each pod derives its partition range from `JOB_COMPLETION_INDEX`, `TOTAL_NODES`, and `TOTAL_PARTITIONS`. The Docker image embeds the model at build time (`HF_HUB_OFFLINE=1` at runtime) so workers never need internet access.

## Prerequisites

- k3s cluster up and `kubectl` configured (default context: `k3s-mbp-rpi`, OrbStack: `orbstack`)
- MinIO running on `192.168.0.33:9000` with a `datasets` bucket
- Docker Hub account (`lester2703`) and `docker login` done before pushing
- Python 3.12+ with `polars` installed locally (for `scripts/prepare.py` and `scripts/split.py`)
- `wget` and `unzip` available (for `scripts/download.sh`)

## Workflow

### 1. Prepare the data

```bash
make download   # fetch all-the-news-2-1.zip from Dropbox into data/
make prepare    # convert CSV to data/article.parquet
make split      # split into 32 partitions and upload to MinIO
```

### 2. Build and push the image

```bash
make build      # docker build -t lester2703/polars-k3s-worker:latest .
make push       # docker login + docker push
```

The image copies `scripts/worker.py` and pre-downloads `all-MiniLM-L6-v2` during build so workers start without network access to Hugging Face Hub.

### 3. Deploy and monitor

```bash
make redeploy   # delete existing Job + kubectl apply job.yaml
make status     # Job completions and pod placement
make logs       # stdout of all worker pods
```

To run on OrbStack instead of the default k3s cluster:

```bash
make use-orbstack   # switch kubectl context to orbstack
make use-k3s        # switch back to k3s-mbp-rpi
```

## Dataset

[All the News 2.0](https://components.one/datasets/all-the-news-2-news-articles-dataset) — 2.7 M English news articles (~2.7 GB CSV). Split into 32 partitions of ~84 k rows each. Each row produces a 384-dimensional float32 embedding vector.

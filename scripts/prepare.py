from pathlib import Path
import polars as pl

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "all-the-news.csv"
PARQUET_PATH = DATA_DIR / "all-the-articles.parquet"


def process_and_save_data(csv_path: Path, parquet_path: Path) -> None:
    df = pl.read_csv(csv_path)
    df.select("article").write_parquet(parquet_path)


if __name__ == "__main__":
    process_and_save_data(CSV_PATH, PARQUET_PATH)

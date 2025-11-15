"""Data cleaning and sentiment analysis ETL."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd

from src.common.config import CURATED_DATA_DIR, RAW_DATA_DIR
from src.common.logging_utils import get_logger
from src.sentiment.analyzer import SentimentAnalyzer


LOGGER = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean and enrich RedBus reviews.")
    parser.add_argument("--input", type=str, default=str(RAW_DATA_DIR))
    parser.add_argument("--output", type=str, default=str(CURATED_DATA_DIR))
    parser.add_argument("--min-rating", type=float, default=0.0)
    parser.add_argument("--parquet", action="store_true", help="Write Parquet as well.")
    return parser.parse_args()


def load_raw_files(input_path: Path) -> pd.DataFrame:
    records: List[pd.DataFrame] = []
    for file in sorted(input_path.glob("*.json")):
        LOGGER.info("Loading %s", file.name)
        df = pd.read_json(file)
        if df.empty:
            continue
        df["source_file"] = file.name
        records.append(df)
    if not records:
        LOGGER.warning("No raw JSON files found in %s", input_path)
        return pd.DataFrame()
    return pd.concat(records, ignore_index=True)


def clean_dataframe(df: pd.DataFrame, min_rating: float) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["review_text"] = (
        df["review_text"].fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df = df[df["review_text"] != ""]
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df[df["rating"].fillna(0) >= min_rating]
    df["review_date"] = pd.to_datetime(
        df["review_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    dedup_cols = ["bus_id", "review_text", "review_date"]
    df = df.drop_duplicates(subset=dedup_cols)

    df["review_length"] = df["review_text"].str.len()
    df["review_word_count"] = df["review_text"].str.split().str.len()
    df["journey_date"] = pd.to_datetime(
        df["journey_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return df


def apply_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    analyzer = SentimentAnalyzer()
    sentiments = df["review_text"].apply(lambda txt: analyzer.analyze(txt))
    df["sentiment"] = sentiments.map(lambda s: s.label)
    df["sentiment_score"] = sentiments.map(lambda s: s.score)
    return df


def aggregate_bus_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    agg = (
        df.groupby("bus_id")
        .agg(
            operator_name=("operator_name", "first"),
            bus_name=("bus_name", "first"),
            bus_type=("bus_type", "first"),
            route=("route", "first"),
            avg_rating=("rating", "mean"),
            rating_count=("rating", "count"),
            sentiment_positive=("sentiment", lambda x: (x == "positive").mean()),
            sentiment_negative=("sentiment", lambda x: (x == "negative").mean()),
        )
        .reset_index()
    )
    return agg


def persist(df_reviews: pd.DataFrame, df_buses: pd.DataFrame, output_dir: Path, parquet: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    reviews_path = output_dir / "reviews.csv"
    buses_path = output_dir / "buses.csv"
    df_reviews.to_csv(reviews_path, index=False)
    df_buses.to_csv(buses_path, index=False)
    LOGGER.info("Wrote reviews -> %s (%s rows)", reviews_path, len(df_reviews))
    LOGGER.info("Wrote buses -> %s (%s rows)", buses_path, len(df_buses))

    if parquet:
        df_reviews.to_parquet(output_dir / "reviews.parquet", index=False)
        df_buses.to_parquet(output_dir / "buses.parquet", index=False)


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.input)
    output_dir = Path(args.output)

    df_raw = load_raw_files(raw_dir)
    cleaned = clean_dataframe(df_raw, min_rating=args.min_rating)
    enriched = apply_sentiment(cleaned)
    bus_metrics = aggregate_bus_metrics(enriched)
    persist(enriched, bus_metrics, output_dir, parquet=args.parquet)


if __name__ == "__main__":
    main()


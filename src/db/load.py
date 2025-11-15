"""Load curated CSVs into the SQLite database."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime

from src.common.config import CURATED_DATA_DIR, DEFAULT_DB_URL
from src.common.logging_utils import get_logger

from .schema import Bus, Review, create_session


LOGGER = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load curated data into SQLite.")
    parser.add_argument("--db", type=str, default=DEFAULT_DB_URL)
    parser.add_argument("--data", type=str, default=str(CURATED_DATA_DIR))
    parser.add_argument("--replace", action="store_true", help="Truncate tables first.")
    return parser.parse_args()


def load_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing curated file: {path}")
    LOGGER.info("Loading %s", path)
    return pd.read_csv(path)


def load_buses(session, buses_df: pd.DataFrame, replace: bool) -> None:
    if replace:
        session.query(Bus).delete()
    bus_models = [
        Bus(
            bus_id=row.bus_id,
            operator_name=row.operator_name,
            bus_name=row.bus_name,
            bus_type=row.bus_type,
            route=row.route,
            avg_rating=row.avg_rating,
            rating_count=int(row.rating_count) if pd.notna(row.rating_count) else None,
        )
        for row in buses_df.itertuples()
    ]
    session.add_all(bus_models)


def load_reviews(session, reviews_df: pd.DataFrame, replace: bool) -> None:
    if replace:
        session.query(Review).delete()

    def parse_date(value: str | float | None):
        if pd.isna(value) or not value:
            return None
        if isinstance(value, datetime):
            return value.date()
        return datetime.strptime(str(value), "%Y-%m-%d").date()

    review_models = [
        Review(
            bus_id=row.bus_id,
            rating=row.rating,
            review_title=row.review_title,
            review_text=row.review_text,
            review_date=parse_date(row.review_date),
            sentiment_label=row.sentiment,
            sentiment_score=row.sentiment_score,
        )
        for row in reviews_df.itertuples()
    ]
    session.add_all(review_models)


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data)
    session = create_session(args.db)

    buses_df = load_dataframe(data_dir / "buses.csv")
    reviews_df = load_dataframe(data_dir / "reviews.csv")

    try:
        load_buses(session, buses_df, replace=args.replace)
        load_reviews(session, reviews_df, replace=args.replace)
        session.commit()
        LOGGER.info("Database load complete.")
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()


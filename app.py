"""Streamlit dashboard for RedBus insights."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import altair as alt
import pandas as pd
import streamlit as st

from src.common.config import CURATED_DATA_DIR, DEFAULT_DB_URL, STREAMLIT_SETTINGS
from src.common.logging_utils import get_logger


LOGGER = get_logger(__name__)


@st.cache_data(ttl=STREAMLIT_SETTINGS.cache_ttl)
def load_curated_data(curated_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    reviews_path = curated_dir / "reviews.csv"
    buses_path = curated_dir / "buses.csv"
    if not reviews_path.exists() or not buses_path.exists():
        st.error("Curated data not found. Run the ETL pipeline first.")
        st.stop()
    reviews = pd.read_csv(reviews_path)
    buses = pd.read_csv(buses_path)
    return reviews, buses


def sidebar_filters(buses_df: pd.DataFrame) -> dict:
    st.sidebar.header("Filters")
    operator = st.sidebar.multiselect(
        "Operator", sorted(buses_df["operator_name"].dropna().unique())
    )
    bus_type = st.sidebar.multiselect(
        "Bus Type", sorted(buses_df["bus_type"].dropna().unique())
    )
    sentiment = st.sidebar.multiselect(
        "Sentiment", ["positive", "neutral", "negative"], default=["positive", "neutral", "negative"]
    )
    rating_range = st.sidebar.slider("Rating range", 0.0, 5.0, (3.0, 5.0), 0.1)
    route_keyword = st.sidebar.text_input("Route keyword")

    return {
        "operator": operator,
        "bus_type": bus_type,
        "sentiment": sentiment,
        "rating_range": rating_range,
        "route_keyword": route_keyword,
    }


def apply_filters(reviews_df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    df = reviews_df.copy()
    if filters["operator"]:
        df = df[df["operator_name"].isin(filters["operator"])]
    if filters["bus_type"]:
        df = df[df["bus_type"].isin(filters["bus_type"])]
    if filters["sentiment"]:
        df = df[df["sentiment"].isin(filters["sentiment"])]
    low, high = filters["rating_range"]
    df = df[df["rating"].between(low, high)]
    if filters["route_keyword"]:
        keyword = filters["route_keyword"].lower()
        df = df[df["route"].str.lower().str.contains(keyword, na=False)]
    return df


def main() -> None:
    st.set_page_config(page_title="RedBus Insights", layout="wide")
    st.title("RedBus Bus Reviews & Sentiment Dashboard")
    st.caption(f"Environment: {STREAMLIT_SETTINGS.env} | DB: {DEFAULT_DB_URL}")

    curated_dir = Path(st.sidebar.text_input("Curated data directory", str(CURATED_DATA_DIR)))
    reviews_df, buses_df = load_curated_data(curated_dir)
    filters = sidebar_filters(buses_df)
    filtered_reviews = apply_filters(reviews_df, filters)

    st.subheader("Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Reviews", len(filtered_reviews))
    col2.metric("Avg Rating", f"{filtered_reviews['rating'].mean():.2f}")
    col3.metric("Positive Share", f"{(filtered_reviews['sentiment'] == 'positive').mean():.0%}")

    st.subheader("Rating Distribution")
    rating_chart = (
        alt.Chart(filtered_reviews)
        .mark_bar()
        .encode(x=alt.X("rating:Q", bin=alt.Bin(step=0.5)), y="count()")
        .properties(height=250)
    )
    st.altair_chart(rating_chart, use_container_width=True)

    st.subheader("Sentiment Breakdown")
    sentiment_chart = (
        alt.Chart(filtered_reviews)
        .mark_arc()
        .encode(theta="count()", color="sentiment")
        .properties(height=300)
    )
    st.altair_chart(sentiment_chart, use_container_width=True)

    st.subheader("Top Buses")
    top_buses = (
        filtered_reviews.groupby(["bus_id", "operator_name", "bus_name"])
        .agg(avg_rating=("rating", "mean"), reviews=("rating", "count"))
        .reset_index()
        .sort_values(by="avg_rating", ascending=False)
        .head(10)
    )
    st.dataframe(top_buses)

    st.subheader("Review Explorer")
    st.dataframe(
        filtered_reviews[
            [
                "operator_name",
                "bus_name",
                "route",
                "rating",
                "sentiment",
                "review_date",
                "review_text",
            ]
        ].sort_values(by="review_date", ascending=False)
    )

    st.subheader("Raw Data Download")
    st.download_button(
        "Download filtered reviews (CSV)",
        filtered_reviews.to_csv(index=False).encode("utf-8"),
        file_name="filtered_reviews.csv",
    )


if __name__ == "__main__":
    main()


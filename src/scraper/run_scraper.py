"""CLI entrypoint for the RedBus scraper."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.common.logging_utils import get_logger
from .redbus_scraper import RedBusScraper


LOGGER = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape RedBus reviews.")
    parser.add_argument(
        "--route",
        required=True,
        help="Comma-separated origin and destination, e.g. 'Chennai,Bangalore'",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of consecutive days (starting today) to fetch results for.",
    )
    parser.add_argument(
        "--headless",
        type=str,
        default=None,
        help="Override headless mode (true/false).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Directory to write raw JSON payloads (defaults to data/raw).",
    )
    return parser.parse_args()


def main() -> Path:
    args = parse_args()
    headless_override = (
        None if args.headless is None else args.headless.lower() == "true"
    )
    scraper = RedBusScraper(
        route=args.route,
        days=args.days,
        headless=headless_override,
        output_dir=Path(args.output) if args.output else None,
    )
    LOGGER.info("Starting scraper for %s (%s days)", args.route, args.days)
    return scraper.scrape()


if __name__ == "__main__":
    main()


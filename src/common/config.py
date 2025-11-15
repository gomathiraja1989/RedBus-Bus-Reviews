"""Global configuration helpers for the RedBus analytics project."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CURATED_DATA_DIR = DATA_DIR / "curated"
LOG_DIR = DATA_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"
DEFAULT_DB_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'redbus.db'}")


for folder in (RAW_DATA_DIR, CURATED_DATA_DIR, LOG_DIR, CACHE_DIR):
    folder.mkdir(parents=True, exist_ok=True)


@dataclass
class ScraperSettings:
    """Options that control the Selenium scraping workflow."""

    headless: bool = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    driver_path: Optional[str] = os.getenv("WEBDRIVER_PATH")
    request_delay: float = float(os.getenv("SCRAPER_DELAY", "1.0"))
    max_scroll_attempts: int = int(os.getenv("SCRAPER_SCROLL_ATTEMPTS", "15"))


@dataclass
class StreamlitSettings:
    env: str = os.getenv("STREAMLIT_ENV", "dev")
    cache_ttl: int = int(os.getenv("STREAMLIT_CACHE_TTL", "600"))


SCRAPER_SETTINGS = ScraperSettings()
STREAMLIT_SETTINGS = StreamlitSettings()


"""Selenium scraper for RedBus listings and reviews."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.common.config import RAW_DATA_DIR, SCRAPER_SETTINGS
from src.common.logging_utils import get_logger
from src.common.utils import read_json, timestamp

from .constants import BASE_URL, DEFAULT_USER_AGENT, SCROLL_PAUSE_SECONDS
from .parsers import parse_bus_card, parse_review


LOGGER = get_logger(__name__)


class RedBusScraper:
    def __init__(
        self,
        route: str,
        days: int,
        headless: Optional[bool] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        self.origin, self.destination = self._parse_route(route)
        self.days = days
        self.output_dir = output_dir or RAW_DATA_DIR
        self.headless = SCRAPER_SETTINGS.headless if headless is None else headless

    @staticmethod
    def _parse_route(route: str) -> tuple[str, str]:
        try:
            origin, destination = [part.strip() for part in route.split(",", 1)]
        except ValueError as exc:
            raise ValueError("Route must be provided as 'Origin,Destination'") from exc
        return origin, destination

    def _driver(self) -> webdriver.Chrome:
        options = ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1440,900")
        options.add_argument(f"user-agent={DEFAULT_USER_AGENT}")
        if self.headless:
            options.add_argument("--headless=new")
        if SCRAPER_SETTINGS.driver_path:
            driver = webdriver.Chrome(
                options=options, service=webdriver.chrome.service.Service(SCRAPER_SETTINGS.driver_path)
            )
        else:
            driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        return driver

    def _search_url(self, journey_date: datetime) -> str:
        doj = journey_date.strftime("%d-%b-%Y").upper()
        return (
            f"{BASE_URL}/search?fromCity={self.origin}&toCity={self.destination}"
            f"&doj={doj}"
        )

    def _scroll_to_bottom(self, driver: webdriver.Chrome) -> None:
        last_height = driver.execute_script("return document.body.scrollHeight")
        attempts = 0
        while attempts < SCRAPER_SETTINGS.max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_SECONDS)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                attempts += 1
            else:
                attempts = 0
                last_height = new_height

    def _collect_bus_cards(self, driver: webdriver.Chrome) -> List[Dict]:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = soup.select(".bus-item")
        LOGGER.info("Found %s bus cards", len(cards))
        return [parse_bus_card(card) for card in cards]

    def _collect_reviews(self, driver: webdriver.Chrome, bus_id: str) -> List[Dict]:
        review_button_selector = f'div[data-busid="{bus_id}"] .rating-sec'
        try:
            button = driver.find_element(By.CSS_SELECTOR, review_button_selector)
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            button.click()
            time.sleep(1.5)
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".review-modal"))
            )
        except Exception:
            LOGGER.debug("No review widget available for %s", bus_id)
            return []

        reviews_html = driver.page_source
        soup = BeautifulSoup(reviews_html, "html.parser")
        review_nodes = soup.select(".review-modal .review-card")
        reviews = [parse_review(node) for node in review_nodes]

        driver.find_element(By.CSS_SELECTOR, ".review-modal .close").click()
        return reviews

    def scrape(self) -> Path:
        payload: List[Dict] = []
        driver: Optional[webdriver.Chrome] = None
        try:
            driver = self._driver()
            for offset in range(self.days):
                journey_date = datetime.today() + timedelta(days=offset)
                url = self._search_url(journey_date)
                LOGGER.info("Opening %s", url)
                driver.get(url)

                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".bus-item"))
                    )
                except TimeoutException:
                    LOGGER.warning("Timed out waiting for bus list on %s", url)
                    continue

                self._scroll_to_bottom(driver)
                buses = self._collect_bus_cards(driver)
                for bus in buses:
                    bus_id = bus.get("bus_id") or ""
                    if not bus_id:
                        continue
                    reviews = self._collect_reviews(driver, bus_id)
                    for review in reviews:
                        payload.append(
                            {
                                **bus,
                                **review,
                                "journey_date": journey_date.strftime("%Y-%m-%d"),
                                "scraped_at": timestamp(),
                            }
                        )
                time.sleep(SCRAPER_SETTINGS.request_delay)
        except WebDriverException as exc:
            LOGGER.error("WebDriver exception: %s", exc)
            raise
        finally:
            if driver is not None:
                driver.quit()

        if not payload:
            sample_path = RAW_DATA_DIR / "sample_reviews.json"
            if sample_path.exists():
                LOGGER.warning(
                    "No live data scraped; falling back to sample payload %s",
                    sample_path,
                )
                payload = read_json(sample_path)
            else:
                LOGGER.warning("No data scraped; returning empty dataset.")

        output_file = self.output_dir / f"redbus_{self.origin}_{self.destination}_{timestamp()}.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)
        LOGGER.info("Persisted %s records -> %s", len(payload), output_file)
        return output_file


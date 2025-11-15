"""BeautifulSoup parsing helpers for bus cards and reviews."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from bs4 import BeautifulSoup


def parse_bus_card(card: BeautifulSoup) -> Dict:
    operator = card.select_one(".travels .name") or card.select_one(".travels")
    bus_name = card.select_one(".bus-name") or card.select_one(".busType")
    bus_type = card.select_one(".bus-type") or card.select_one(".busType")
    rating = card.select_one(".rating-sec .rating") or card.select_one(".rating")
    rating_count = card.select_one(".rating-sec .votes")
    route = card.select_one(".route-info") or card.select_one(".route")

    return {
        "bus_id": card.get("data-busid") or card.get("id"),
        "operator_name": operator.get_text(strip=True) if operator else None,
        "bus_name": bus_name.get_text(strip=True) if bus_name else None,
        "bus_type": bus_type.get_text(strip=True) if bus_type else None,
        "rating": _safe_float(rating.get_text(strip=True)) if rating else None,
        "rating_count": _safe_int(_safe_digits(rating_count.get_text()))
        if rating_count
        else None,
        "route": route.get_text(strip=True) if route else None,
    }


def parse_review(review_node: BeautifulSoup) -> Dict:
    rating = review_node.select_one(".rating") or review_node.select_one(".score")
    title = review_node.select_one(".title")
    body = review_node.select_one(".comment") or review_node.select_one(".desc")
    date = review_node.select_one(".review-date") or review_node.select_one(".date")

    return {
        "rating": _safe_float(rating.get_text(strip=True)) if rating else None,
        "review_title": title.get_text(strip=True) if title else None,
        "review_text": body.get_text(strip=True) if body else None,
        "review_date": _format_review_date(date.get_text(strip=True)) if date else None,
    }


def _safe_float(value: Optional[str]) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Optional[str]) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_digits(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or None


def _format_review_date(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


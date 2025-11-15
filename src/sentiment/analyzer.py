"""Simple sentiment analyzer wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


@lru_cache(maxsize=1)
def _vader() -> SentimentIntensityAnalyzer:
    return SentimentIntensityAnalyzer()


@dataclass
class SentimentResult:
    label: str
    score: float


class SentimentAnalyzer:
    POSITIVE_THRESHOLD = 0.05
    NEGATIVE_THRESHOLD = -0.05

    @staticmethod
    def analyze(text: str) -> SentimentResult:
        if not text:
            return SentimentResult(label="neutral", score=0.0)

        scores: Dict[str, float] = _vader().polarity_scores(text)
        compound = scores["compound"]

        if compound >= SentimentAnalyzer.POSITIVE_THRESHOLD:
            label = "positive"
        elif compound <= SentimentAnalyzer.NEGATIVE_THRESHOLD:
            label = "negative"
        else:
            label = "neutral"

        return SentimentResult(label=label, score=compound)


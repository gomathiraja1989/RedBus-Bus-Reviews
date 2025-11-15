"""Shared helper functions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List, Sequence


def timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def chunked(seq: Sequence[Any], size: int) -> Iterable[List[Any]]:
    for idx in range(0, len(seq), size):
        yield list(seq[idx : idx + size])


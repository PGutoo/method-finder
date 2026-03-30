"""Load curated sample Materials-and-Methods excerpts for the UI."""

from __future__ import annotations

import json
from typing import Any

from method_finder.paths import REPO_ROOT


def load_sample_input_records() -> list[dict[str, Any]]:
    path = REPO_ROOT / "db" / "sample_input.json"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError, TypeError):
        return []

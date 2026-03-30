"""Load DB-ALM catalogue CSV into memory as a pandas DataFrame."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from method_finder.paths import REPO_ROOT

_DEFAULT_CATALOGUE_PATH = REPO_ROOT / "db" / "DBALM_Catalogue.csv"

_CATALOGUE: pd.DataFrame | None = None

_TITLE_SUMMARY_SUFFIX = " - Summary"


def _strip_title_suffix(val: object) -> object:
    if pd.isna(val):
        return val
    s = str(val).strip()
    if s.endswith(_TITLE_SUMMARY_SUFFIX):
        s = s[: -len(_TITLE_SUMMARY_SUFFIX)].rstrip()
    return s


def _split_biological_endpoints(text: object) -> list[str]:
    if pd.isna(text):
        return []
    raw = str(text)
    if not raw.strip():
        return []
    normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
    return [line.strip() for line in normalized.split("\n") if line.strip()]


def _clean_cell_to_list(text: object) -> list[str]:
    if pd.isna(text) or text == "" or text == " ":
        return []
    items = re.split(r"\n|\t|\r|\s{2,}", str(text))
    return [item.strip() for item in items if item.strip()]


def parse_alm_database(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    df = pd.read_csv(path, engine="python")
    df.columns = [col.strip() for col in df.columns]

    if "Title" in df.columns:
        df["Title"] = df["Title"].apply(_strip_title_suffix)

    list_columns = [
        "Topic area",
        "Models and Strategies",
        "Experimental systems",
    ]
    for col in list_columns:
        if col in df.columns:
            df[col] = df[col].apply(_clean_cell_to_list)

    if "Biological endpoints" in df.columns:
        df["Biological endpoints"] = df["Biological endpoints"].apply(_split_biological_endpoints)

    reg_col = "Regulatory  information"
    no_col = "No."

    def determine_status(row: pd.Series) -> str:
        try:
            val = str(row[no_col]).strip()
            if val != "0" and val.isdigit():
                return f"Validated (OECD/EURL-ECVAM #{val})"
            reg = str(row.get(reg_col, "") or "").lower()
            if "tsar" in reg:
                return "Regulatory Submission Underway"
            return "Scientific Alternative (R&D Use)"
        except Exception:
            return "Informational"

    df["validation_tier"] = df.apply(determine_status, axis=1)

    def search_blob_row(x: pd.Series) -> str:
        title = x.get("Title")
        title_s = "" if pd.isna(title) else str(title).strip()
        topics = x["Topic area"] if "Topic area" in x.index else []
        bio = x["Biological endpoints"] if "Biological endpoints" in x.index else []
        if not isinstance(topics, list):
            topics = _clean_cell_to_list(topics)
        if not isinstance(bio, list):
            bio = _split_biological_endpoints(bio)
        return " ".join([title_s, *topics, *bio]).lower()

    df["search_blob"] = df.apply(search_blob_row, axis=1)

    return df


def load_catalogue(file_path: str | Path | None = None) -> pd.DataFrame:
    """Parse CSV and store the in-memory catalogue."""
    global _CATALOGUE
    path = Path(file_path) if file_path is not None else _DEFAULT_CATALOGUE_PATH
    _CATALOGUE = parse_alm_database(path)
    return _CATALOGUE


def get_catalogue() -> pd.DataFrame:
    """Return loaded catalogue, loading from default path if needed."""
    if _CATALOGUE is None:
        load_catalogue()
    assert _CATALOGUE is not None
    return _CATALOGUE


if __name__ == "__main__":
    db = parse_alm_database(_DEFAULT_CATALOGUE_PATH)
    print(f"Successfully loaded {len(db)} methods into memory.")

"""Parse protocol JSON from the LLM and match rows in the DB-ALM catalogue."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from method_finder.domain.topic_mapping import TopicNormalizer
from method_finder.paths import REPO_ROOT

__all__ = [
    "parse_protocol_json",
    "PROTOCOL_BRIDGE",
    "load_protocol_bridge",
    "filter_catalogue_by_topic",
    "compute_match_score",
    "compute_match_breakdown",
    "enrich_protocol_with_catalogue",
    "clamp_top_matches",
    "DEFAULT_TOP_MATCHES_PER_SECTION",
    "regulatory_authority_tier",
    "endpoint_coverage_tier",
]

_DEFAULT_BRIDGE_JSON = REPO_ROOT / "db" / "protocol_bridge.json"

# --- A. Regulatory authority (Ethics / "Authority" check): 3 = high, 2 = medium, 1 = low ---

_OECD_TG_RE = re.compile(
    r"\b(?:oecd\s*)?tg\s*\d{2,4}[a-z]?\b"
    r"|\btest\s+guideline\s*(?:no\.?|number)?\s*\d{2,4}\b"
    r"|\boecd\s+(?:test\s+)?guideline\s*\d+",
    re.IGNORECASE,
)

# --- B. Endpoint proxy groups (protocol language ↔ catalogue / alternative language) ---

_ENDPOINT_PROXY_GROUPS: tuple[dict[str, tuple[str, ...]], ...] = (
    {
        "protocol": ("alt", "ast", "serum", "biochemistry", "hepatic", "transaminase", "liver enzyme"),
        "catalogue": (
            "viability",
            "hepatotoxicity",
            "hepatocyte",
            "liver",
            "metabolic",
            "mtt",
            "luminescence",
            "atp",
            "hepa",
        ),
    },
    {
        "protocol": ("sensitization", "sensitisation", "allerg", "skin sensit"),
        "catalogue": (
            "gene",
            "expression",
            "cytokine",
            "il-18",
            "il-8",
            "rna",
            "transcript",
            "genomic",
        ),
    },
    {
        "protocol": ("ld50", "lethal", "acute oral", "acute toxicity"),
        "catalogue": (
            "basal cytotoxicity",
            "ic50",
            "prediction",
            "qsar",
            "neutral red",
            "uptake",
            "nru",
            "3t3",
        ),
    },
    {
        "protocol": ("histology", "pathology", "tissue", "lesion", "microscopy"),
        "catalogue": (
            "morpholog",
            "microscop",
            "stain",
            "architecture",
            "organoid",
            "organ-on-a-chip",
            "chip",
            "pathological",
        ),
    },
    {
        "protocol": ("tumor", "tumour", "neoplasm", "carcinogen", "malignancy"),
        "catalogue": (
            "transformation",
            "bhas",
            "cell transformation",
            "genotoxic",
            "mutation",
        ),
    },
)

_ASSAY_MARKERS = frozenset(
    {
        "ld50",
        "ic50",
        "ec50",
        "mtt",
        "nru",
        "neutral",
        "red",
        "alt",
        "ast",
        "cytokine",
        "erythema",
        "corneal",
        "tumor",
        "tumour",
        "viability",
        "histology",
        "mutation",
    }
)


_WRAPPER_SUMMARY_KEYS = frozenset({"study_summary", "input_summary"})
_WRAPPER_LIST_KEYS = ("experiments", "protocol_sections")


def load_protocol_bridge(path: Path | None = None) -> dict[str, Any]:
    """
    Load unified protocol→Topic area bridge from JSON.

    **groups**: map of group id -> list of catalogue Topic area keywords.
    **rules**: each rule has **match** ``substring`` | ``label``, **text** (trigger),
    and either **group** (id into groups) or **keywords** (inline list).

    - **substring**: ``text.lower()`` must appear in the section search blob (domain,
      normalized domain, test description, endpoints).
    - **label**: **text** must overlap the raw or normalized domain (substring either way).
    """
    p = path or _DEFAULT_BRIDGE_JSON
    try:
        with open(p, encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError, TypeError):
        return {"groups": {}, "rules": []}
    if not isinstance(raw, dict):
        return {"groups": {}, "rules": []}

    groups_out: dict[str, tuple[str, ...]] = {}
    gr = raw.get("groups")
    if isinstance(gr, dict):
        for gid, val in gr.items():
            gkey = str(gid).strip()
            if not gkey or not isinstance(val, list):
                continue
            tup = tuple(str(x).strip() for x in val if str(x).strip())
            if tup:
                groups_out[gkey] = tup

    rules_out: list[dict[str, Any]] = []
    rules = raw.get("rules")
    if isinstance(rules, list):
        for item in rules:
            if not isinstance(item, dict):
                continue
            m = str(item.get("match", "substring")).strip().lower()
            if m not in ("substring", "label"):
                continue
            text = item.get("text")
            if text is None or not str(text).strip():
                continue
            rule: dict[str, Any] = {"match": m, "text": str(text).strip()}
            if "keywords" in item and isinstance(item["keywords"], list):
                kws = [str(x).strip() for x in item["keywords"] if str(x).strip()]
                if kws:
                    rule["keywords"] = kws
            gid = item.get("group")
            if gid is not None and str(gid).strip():
                rule["group"] = str(gid).strip()
            if "keywords" not in rule and "group" not in rule:
                continue
            rules_out.append(rule)

    return {"groups": groups_out, "rules": rules_out}


PROTOCOL_BRIDGE: dict[str, Any] = load_protocol_bridge()


def _expand_bridge_rules(
    groups: dict[str, tuple[str, ...]],
    rules: list[dict[str, Any]],
    *,
    normalized_domain: str,
    raw_domain: str,
    synonym_blob: str,
    keywords: set[str],
) -> None:
    nds = str(normalized_domain or "").strip()
    raws = str(raw_domain or "").strip()
    blob = (synonym_blob or "").lower()

    for rule in rules:
        m = rule["match"]
        text = rule["text"]
        if m == "substring":
            needle = text.strip().lower()
            if not needle or needle not in blob:
                continue
        else:
            if not (_label_pair_overlaps(text, nds) or _label_pair_overlaps(text, raws)):
                continue

        for kw in rule.get("keywords") or ():
            keywords.add(kw.lower())
        gid = rule.get("group")
        if gid and gid in groups:
            for kw in groups[gid]:
                keywords.add(kw.lower())


def _build_synonym_search_blob(
    section: dict[str, Any],
    normalized_domain: str,
    raw_domain: str,
) -> str:
    """Lowercase blob for ``substring`` rules in ``db/protocol_bridge.json``."""
    parts: list[str] = [raw_domain or "", normalized_domain or ""]
    td = section.get("test_description")
    if td is not None and str(td).strip():
        parts.append(str(td))
    em = section.get("endpoints_measured")
    if isinstance(em, list):
        parts.extend(str(x) for x in em if x is not None and str(x).strip())
    elif em is not None and str(em).strip():
        parts.append(str(em))
    return " ".join(parts).lower()


def _label_pair_overlaps(a: str, b: str) -> bool:
    x = (a or "").strip().lower()
    y = (b or "").strip().lower()
    if not x or not y:
        return False
    return x in y or y in x


def _topic_keywords_for_domains(
    normalized_domain: str,
    raw_domain: str,
    *,
    synonym_blob: str = "",
) -> frozenset[str]:
    """Search terms for Topic area: normalized/raw text plus ``protocol_bridge.json`` rules."""
    nd = str(normalized_domain or "").strip()
    rd = str(raw_domain or "").strip().lower()
    keywords: set[str] = set()
    if nd:
        keywords.add(nd.lower())
    if rd:
        keywords.add(rd)

    br = PROTOCOL_BRIDGE
    _expand_bridge_rules(
        br.get("groups") or {},
        br.get("rules") or [],
        normalized_domain=nd,
        raw_domain=str(raw_domain or "").strip(),
        synonym_blob=synonym_blob,
        keywords=keywords,
    )

    return frozenset(kw for kw in keywords if len(kw) >= 2)


def parse_protocol_json(raw: str) -> tuple[list[dict[str, Any]], str]:
    """
    Parse assistant output into protocol section dicts and an optional study summary.

    Supported shapes:
    - {"study_summary": "...", "experiments": [ {...}, ... ]} (preferred)
    - [ {...}, ... ] — legacy list of experiment objects (summary "")
    - Single experiment object without wrapper — legacy (summary "")

    Strips optional ```json ... ``` fences.
    """
    text = (raw or "").strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()

    data = json.loads(text)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)], ""

    if isinstance(data, dict):
        summary = ""
        for sk in _WRAPPER_SUMMARY_KEYS:
            v = data.get(sk)
            if v is not None and str(v).strip():
                summary = str(v).strip()
                break

        for lk in _WRAPPER_LIST_KEYS:
            arr = data.get(lk)
            if isinstance(arr, list):
                return [x for x in arr if isinstance(x, dict)], summary

        noise = _WRAPPER_SUMMARY_KEYS | frozenset(_WRAPPER_LIST_KEYS)
        if any(
            k in data
            for k in ("section_id", "domain", "test_description", "species", "endpoints_measured")
        ):
            section = {k: v for k, v in data.items() if k not in noise}
            if section:
                return [section], summary

        if summary:
            return [], summary

        raise ValueError(
            "Protocol JSON must include an 'experiments' array or a legacy experiment object"
        )

    raise ValueError("Protocol JSON must be a JSON object or array")


def _topic_area_values(row: pd.Series) -> list[str]:
    cell = row["Topic area"] if "Topic area" in row.index else None
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    if isinstance(cell, list):
        return [str(t).strip() for t in cell if str(t).strip()]
    s = str(cell).strip()
    return [s] if s else []


def _list_cell(row: pd.Series, col: str) -> list[str]:
    cell = row[col] if col in row.index else None
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    if isinstance(cell, list):
        return [str(t).strip() for t in cell if str(t).strip()]
    s = str(cell).strip()
    return [s] if s else []


def _topic_domain_overlaps(
    normalized_domain: str,
    raw_domain: str,
    row: pd.Series,
    *,
    synonym_blob: str = "",
) -> bool:
    kws = _topic_keywords_for_domains(
        normalized_domain, raw_domain, synonym_blob=synonym_blob
    )
    if not kws:
        return False
    for t in _topic_area_values(row):
        tl = t.lower()
        for kw in kws:
            if kw in tl or tl in kw:
                return True
    return False


def _protocol_endpoints_measured_parsed(section: dict[str, Any]) -> tuple[str, list[str]]:
    """Lowercase search blob and token list from protocol endpoints_measured."""
    em = section.get("endpoints_measured")
    if em is None:
        return "", []
    if isinstance(em, list):
        parts = [str(x).strip().lower() for x in em if str(x).strip()]
    else:
        raw = str(em).lower()
        parts = [p.strip() for p in re.split(r"[,;]|\n", raw) if p.strip()]
    blob = " ".join(parts)
    return blob, parts


def _tokenize(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2}


def _tsv_endpoint_in_protocol(tsv_ep: str, blob: str, protocol_parts: list[str]) -> bool:
    te = tsv_ep.strip().lower()
    if len(te) < 2:
        return False
    if te in blob:
        return True
    for p in protocol_parts:
        if len(p) < 2:
            continue
        if te in p or p in te:
            return True
    return False


def _no_column_positive(row: pd.Series) -> bool:
    if "No." not in row.index:
        return False
    v = row["No."]
    if pd.isna(v):
        return False
    s = str(v).strip()
    return s.isdigit() and int(s) > 0


def _regulatory_scan_text(row: pd.Series) -> str:
    chunks: list[str] = []
    for col in (
        "Title",
        "Regulatory  information",
        "Supplementary materials (Downloads)",
        "Document type",
        "validation_tier",
        "EUProject",
    ):
        if col not in row.index:
            continue
        v = row[col]
        if pd.notna(v):
            chunks.append(str(v))
    return " ".join(chunks).lower()


def regulatory_authority_tier(row: pd.Series) -> tuple[int, str]:
    """
    A. Regulatory validation (authority for ethics committees).

    Returns (points, tier_name):
    - (3, 'high'): OECD Test Guideline (TG) number present in catalogue text.
    - (2, 'medium'): EURL ECVAM / TSAR validated listing without TG in text,
      or DB-ALM validated method number (No. > 0) without TG.
    - (1, 'low'): Scientific / research use (e.g. NC3Rs, R&D), default when not above.
    """
    text = _regulatory_scan_text(row)
    vtier = str(row.get("validation_tier", "") or "").lower()

    if _OECD_TG_RE.search(text):
        return 3, "high"

    if _no_column_positive(row):
        return 2, "medium"

    if "tsar" in text and "valid" in text:
        return 2, "medium"
    if "eurl" in text and "ecvam" in text:
        return 2, "medium"
    if "validated" in vtier and ("oecd" in vtier or "ecvam" in vtier or "eurl" in vtier):
        return 2, "medium"

    if "nc3rs" in text or "scientific alternative" in vtier or "r&d" in vtier:
        return 1, "low"

    return 1, "low"


def _endpoint_coverage_pair_score(tsv_ep: str, blob: str, protocol_parts: list[str]) -> int:
    """
    B. Endpoint coverage for one catalogue biological endpoint vs protocol.

    Returns 3 = full, 2 = partial, 1 = proxy, 0 = none.
    """
    te = tsv_ep.strip().lower()
    if len(te) < 2:
        return 0

    prot_tokens = _tokenize(blob + " " + " ".join(protocol_parts))
    ep_tokens = _tokenize(tsv_ep)

    if _tsv_endpoint_in_protocol(tsv_ep, blob, protocol_parts):
        shared = prot_tokens & ep_tokens
        if (shared & _ASSAY_MARKERS) or len(shared) >= 2 or (len(te) >= 10 and te in blob):
            return 3
        return 2

    if ep_tokens and prot_tokens:
        inter = ep_tokens & prot_tokens
        union = ep_tokens | prot_tokens
        j = len(inter) / len(union) if union else 0.0
        if j >= 0.18 or len(inter) >= 2:
            return 2

    for group in _ENDPOINT_PROXY_GROUPS:
        prot_hits = any(k in blob for k in group["protocol"])
        cat_hits = any(k in te for k in group["catalogue"])
        rev_prot = any(k in te for k in group["protocol"])
        rev_cat = any(k in blob for k in group["catalogue"])
        if (prot_hits and cat_hits) or (rev_prot and rev_cat):
            return 1

    return 0


def endpoint_coverage_tier(section: dict[str, Any], row: pd.Series) -> tuple[int, str]:
    """
    B. Best endpoint coverage across all Biological endpoints for this catalogue row.

    full (3): same or directly equivalent measure (e.g. LD50 vs LD50 / NRU prediction).
    partial (2): overlapping biology but not equivalent (e.g. serum enzymes vs viability).
    proxy (1): correlated / mechanistic proxy via curated keyword groups.
    none (0): no usable overlap.
    """
    blob, parts = _protocol_endpoints_measured_parsed(section)
    if not blob.strip() and not parts:
        return 0, "none"

    tsv_eps = _list_cell(row, "Biological endpoints")
    if not tsv_eps:
        return 0, "none"

    best = 0
    for ts in tsv_eps:
        s = _endpoint_coverage_pair_score(ts, blob, parts)
        if s > best:
            best = s
        if best == 3:
            break

    labels = {3: "full", 2: "partial", 1: "proxy", 0: "none"}
    return best, labels[best]


def _match_score_0_100(auth_pts: int, end_pts: int) -> int:
    """
    Map (regulatory 1–3, endpoint 0–3) to 0–100 while preserving the same sort order as
    auth*100+endpoint (lexicographic: authority first, then endpoint).
    """
    rank = (auth_pts - 1) * 4 + end_pts  # 0 .. 11
    return int(round(100 * rank / 11))


def compute_match_breakdown(
    section: dict[str, Any],
    catalogue_row: pd.Series,
) -> dict[str, Any]:
    """
    Combined score for sorting: regulatory authority dominates, then endpoint coverage.

    ``match_score`` is 0–100 (not a calibrated probability): it linearly maps the 12
    discrete (authority, endpoint) combinations to the unit interval, preserving the
    ordering of the legacy key ``authority × 100 + endpoint``.
    """
    auth_pts, auth_label = regulatory_authority_tier(catalogue_row)
    end_pts, end_label = endpoint_coverage_tier(section, catalogue_row)
    return {
        "match_score": _match_score_0_100(auth_pts, end_pts),
        "regulatory_authority_score": auth_pts,
        "regulatory_authority_tier": auth_label,
        "endpoint_coverage_score": end_pts,
        "endpoint_coverage_tier": end_label,
    }


def compute_match_score(
    section: dict[str, Any],
    catalogue_row: pd.Series,
) -> int:
    """Single scalar for sorting; see compute_match_breakdown for components."""
    return int(compute_match_breakdown(section, catalogue_row)["match_score"])


def filter_catalogue_by_topic(
    df: pd.DataFrame,
    normalized_domain: str,
    raw_domain: str = "",
    *,
    synonym_blob: str = "",
) -> pd.DataFrame:
    """
    Rows where any value in **Topic area** matches the normalized/raw domain or any
    related keywords from ``db/protocol_bridge.json`` (groups + rules)
    (substring, case-insensitive).
    """
    if df is None or df.empty:
        return df.iloc[0:0].copy() if df is not None else pd.DataFrame()

    nd = str(normalized_domain or "").strip()
    rd = str(raw_domain or "").strip()
    if not nd and not rd and not (synonym_blob or "").strip():
        return df.iloc[0:0].copy()

    domain_arg = nd
    raw_arg = rd
    syn_arg = synonym_blob or ""

    def row_matches(row: pd.Series) -> bool:
        return _topic_domain_overlaps(
            domain_arg, raw_arg, row, synonym_blob=syn_arg
        )

    return df[df.apply(row_matches, axis=1)]


DEFAULT_TOP_MATCHES_PER_SECTION = 5
MIN_TOP_MATCHES_PER_SECTION = 3
MAX_TOP_MATCHES_PER_SECTION = 5


def clamp_top_matches(n: int) -> int:
    """Clamp catalogue rows per protocol section to the allowed range (3–5)."""
    return max(MIN_TOP_MATCHES_PER_SECTION, min(MAX_TOP_MATCHES_PER_SECTION, int(n)))


def enrich_protocol_with_catalogue(
    protocol_sections: list[dict[str, Any]],
    df: pd.DataFrame,
    normalizer: TopicNormalizer | None = None,
    max_hits_per_section: int = DEFAULT_TOP_MATCHES_PER_SECTION,
) -> list[dict[str, Any]]:
    """
    For each protocol section, set normalized_domain and catalogue matches
    derived from TopicNormalizer + Topic area on the catalogue DataFrame.
    """
    n = normalizer or TopicNormalizer()
    out: list[dict[str, Any]] = []

    hit_cols = [
        c
        for c in (
            "Title",
            "No.",
            "validation_tier",
            "Regulatory  information",
            "Supplementary materials (Downloads)",
        )
        if c in df.columns
    ]

    for section in protocol_sections:
        raw_domain = section.get("domain", "")
        if raw_domain is None:
            raw_domain = ""
        if not isinstance(raw_domain, str):
            raw_domain = str(raw_domain)

        normalized_domain = n.normalize(raw_domain)
        syn_blob = _build_synonym_search_blob(section, normalized_domain, raw_domain)
        matches = filter_catalogue_by_topic(
            df, normalized_domain, raw_domain, synonym_blob=syn_blob
        )

        scored: list[tuple[int, dict[str, Any]]] = []
        for _, row in matches.iterrows():
            breakdown = compute_match_breakdown(section, row)
            rec: dict[str, Any] = dict(breakdown)
            for c in hit_cols:
                val = row[c]
                if pd.isna(val):
                    rec[c] = None
                elif c == "No." and str(val).strip().isdigit():
                    rec[c] = int(str(val).strip())
                else:
                    rec[c] = val
            scored.append((breakdown["match_score"], rec))

        scored.sort(key=lambda x: -x[0])
        catalogue_hits = [rec for _, rec in scored[:max_hits_per_section]]

        enriched = {
            **section,
            "normalized_domain": normalized_domain,
            "catalogue_match_count": int(len(matches)),
            "catalogue_hits": catalogue_hits,
        }
        out.append(enriched)

    return out

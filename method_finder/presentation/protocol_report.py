"""Markdown report in the style of mock_output.md for enriched protocol + DB-ALM matches."""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import quote_plus

DBALM_METHOD_BASE = "https://purl.jrc.ec.europa.eu/dataset/db-alm/method"
OECD_CHEMICALS_TOPIC_URL = (
    "https://www.oecd.org/en/topics/sub-issues/assessment-of-chemicals.html"
)

_OECD_TG_NUM_PATTERNS = (
    re.compile(r"\btg\s*(\d{2,4}[a-z]?)\b", re.IGNORECASE),
    re.compile(
        r"\btest\s+guideline\s*(?:no\.?|number)?\s*(\d{2,4}[a-z]?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\boecd\s*(?:tg|test\s+guideline)\s*(\d{2,4}[a-z]?)\b",
        re.IGNORECASE,
    ),
)

_HTTP_URL_RE = re.compile(r"https?://[^\s\]\)<>\"']+", re.IGNORECASE)

_TSAR_PORTAL_URL = "https://tsar.jrc.ec.europa.eu/"


def _md_cell(val: Any) -> str:
    if val is None:
        return "—"
    s = str(val).replace("\n", " ").replace("|", "/").replace("*", "").strip()
    return s if s else "—"


def _dbalm_source_link(hit: dict[str, Any]) -> str:
    no = hit.get("No.")
    if no is not None and str(no).strip().isdigit() and int(str(no).strip()) > 0:
        n = int(str(no).strip())
        return f"[DB-ALM-{n}]({DBALM_METHOD_BASE}/{n})"
    return "[DB-ALM catalogue](https://cm.jrc.ec.europa.eu/core-databases/db-alm/)"


def _oecd_ilibrary_search_url(tg_id: str) -> str:
    """OECD iLibrary search for a test guideline number (pattern requested by product)."""
    tid = str(tg_id).strip()
    q = f"test no. {tid}"
    return f"https://www.oecd-ilibrary.org/search?q={quote_plus(q)}"


def _hit_field_str(hit: dict[str, Any], key: str) -> str:
    v = hit.get(key)
    if v is None:
        return ""
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return ""
    return s


def _extract_http_urls(*text_parts: str) -> list[str]:
    """Ordered unique HTTP(S) URLs from catalogue text fields."""
    blob = " ".join(str(p) for p in text_parts if p)
    seen: dict[str, None] = {}
    out: list[str] = []
    for m in _HTTP_URL_RE.finditer(blob):
        u = m.group(0).rstrip(".,;)")
        if u not in seen:
            seen[u] = None
            out.append(u)
    return out


def _tsar_urls(urls: list[str]) -> list[str]:
    return [u for u in urls if "tsar.jrc" in u.lower()]


def _collect_oecd_tg_ids(*text_parts: str) -> list[str]:
    """Unique TG / test guideline numbers found in catalogue text (stable order)."""
    blob = " ".join(str(p) for p in text_parts if p)
    seen: dict[str, None] = {}
    for pat in _OECD_TG_NUM_PATTERNS:
        for m in pat.finditer(blob):
            raw = m.group(1).strip()
            key = raw.upper() if raw[-1:].isalpha() else raw
            if key not in seen:
                seen[key] = None
    return list(seen.keys())


def _regulatory_links_cell(hit: dict[str, Any]) -> str:
    """
    Ethics-oriented link order:

    1. **OECD standard (iLibrary)** — primary when an OECD TG / test guideline number
       is found in title, validation tier, or regulatory text (what regulators expect first).
    2. **Validation background** — TSAR URL from catalogue regulatory / supplementary
       fields (EURL ECVAM method record).
    3. **TSAR-only** — when there is no OECD TG signal but a TSAR link or TSAR context
       exists, TSAR is the main regulatory anchor.
    """
    parts: list[str] = [_dbalm_source_link(hit)]

    title = _hit_field_str(hit, "Title")
    vt = _hit_field_str(hit, "validation_tier")
    reg = _hit_field_str(hit, "Regulatory  information")
    supp = _hit_field_str(hit, "Supplementary materials (Downloads)")

    tg_ids = _collect_oecd_tg_ids(title, vt, reg, supp)
    all_urls = _extract_http_urls(reg, supp)
    tsar_list = _tsar_urls(all_urls)
    reg_lower = reg.lower()
    mentions_tsar = "tsar" in reg_lower or "tsar" in supp.lower()

    if tg_ids:
        oecd_bits = [
            f"[OECD TG {tid} (standard, OECD iLibrary)]({_oecd_ilibrary_search_url(tid)})"
            for tid in tg_ids
        ]
        parts.append("**OECD standard:** " + ", ".join(oecd_bits))
        if tsar_list:
            parts.append(
                f"**Validation background:** [TSAR method record]({tsar_list[0]})"
            )
        return " · ".join(parts)

    if tsar_list:
        parts.append(
            f"**Regulatory (TSAR):** [TSAR validated method]({tsar_list[0]})"
        )
        return " · ".join(parts)

    if mentions_tsar and ("valid" in reg_lower or "eurl" in reg_lower or "ecvam" in reg_lower):
        parts.append(
            f"**Regulatory (TSAR):** [TSAR / EURL ECVAM records]({_TSAR_PORTAL_URL})"
        )
        return " · ".join(parts)

    return " · ".join(parts)


def _validation_cell_with_oecd(vt: Any) -> str:
    """
    Validation (DB-ALM) cell: link TG / test-guideline mentions to OECD iLibrary search,
    and bare OECD mentions to the OECD chemicals assessment topic page.

    OECD word links are applied before TG links so we do not match ``oecd`` inside
    iLibrary URLs added for test guidelines.
    """
    if vt is None:
        return "—"
    s = str(vt).replace("\n", " ").replace("|", "/").strip()
    if not s:
        return "—"

    def _oecd_word_link(m: re.Match[str]) -> str:
        return f"[{m.group(1)}]({OECD_CHEMICALS_TOPIC_URL})"

    s = re.sub(
        r"(?<!\[)\b(OECD)\b",
        _oecd_word_link,
        s,
        flags=re.IGNORECASE,
    )

    spans: list[tuple[int, int, str]] = []
    for pat in _OECD_TG_NUM_PATTERNS:
        for m in pat.finditer(s):
            raw = m.group(1).strip()
            key = raw.upper() if raw[-1:].isalpha() else raw
            spans.append((m.start(), m.end(), key))
    spans.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    merged: list[tuple[int, int, str]] = []
    for start, end, tid in spans:
        if merged and start < merged[-1][1]:
            continue
        merged.append((start, end, tid))

    if merged:
        cursor = len(s)
        parts: list[str] = []
        for start, end, tid in reversed(merged):
            label = s[start:end]
            link = f"[{label}]({_oecd_ilibrary_search_url(tid)})"
            parts.insert(0, s[end:cursor])
            parts.insert(0, link)
            cursor = start
        parts.insert(0, s[:cursor])
        out = "".join(parts)
    else:
        out = s

    out = out.replace("*", "")
    return out if out.strip() else "—"


def _listish_to_cell(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, list):
        return "; ".join(str(x).strip() for x in val if x is not None and str(x).strip())
    return str(val).strip()


def _regulatory_cell(val: Any) -> str:
    if val is True:
        return "Yes"
    if val is False:
        return "No"
    return _md_cell(val)


def _category_display(sec: dict[str, Any]) -> str:
    c = sec.get("category")
    if c is not None and str(c).strip():
        return str(c).strip()
    return str(sec.get("domain") or "").strip()


def _vertical_parameter_rows(
    sec: dict[str, Any],
    *,
    include_section_id_row: bool = False,
) -> list[tuple[str, str]]:
    """(label, value) pairs for one experiment; values are markdown-safe cells."""
    sid = _md_cell(sec.get("section_id"))
    cat = _md_cell(_category_display(sec))
    mt = _md_cell(sec.get("model_type"))
    alt = _regulatory_cell(sec.get("is_alternative_method"))
    spec = _md_cell(sec.get("species"))
    strain = _md_cell(sec.get("strain"))
    sex = _md_cell(sec.get("sex"))
    n = _md_cell(sec.get("sample_size"))
    route = _md_cell(sec.get("administration_route"))
    dur = _md_cell(sec.get("duration"))
    organs = _listish_to_cell(sec.get("organs_or_tissues"))
    organs_c = _md_cell(organs if organs else "—")
    eps = _listish_to_cell(sec.get("endpoints_measured"))
    ep_c = _md_cell(eps if eps else "—")
    reg = _regulatory_cell(sec.get("is_regulatory_standard"))
    article = _md_cell(sec.get("test_article"))
    proc = _md_cell(sec.get("test_description"))

    rows: list[tuple[str, str]] = []
    if include_section_id_row:
        rows.append(("Section", sid))
    rows.extend(
        [
            ("Category", cat),
            ("Model type", mt if mt else "—"),
            ("3Rs / alternative method", alt),
            ("Species", spec),
            ("Strain", strain),
            ("Sex", sex),
            ("Animals (n)", n),
            ("Route", route),
            ("Duration", dur),
            ("Organs / tissues", organs_c),
            ("Endpoints", ep_c),
            ("Regulatory reference", reg),
            ("Test article", article),
            ("Procedure", proc if proc else "—"),
        ]
    )
    return rows


def _format_section_parameters_markdown(sec: dict[str, Any]) -> str:
    """Vertical Parameter | Value table for one section (placed under that section's heading)."""
    lines = [
        "### Extracted parameters",
        "",
        "| Parameter | Value |",
        "| :--- | :--- |",
    ]
    for label, val in _vertical_parameter_rows(sec, include_section_id_row=False):
        lines.append(f"| **{label}** | {val} |")
    lines.append("")
    return "\n".join(lines)


def format_protocol_report_markdown(
    enriched_sections: list[dict[str, Any]],
    *,
    study_summary: str = "",
) -> str:
    """
    Build a report similar to method_finder/infrastructure/mock_output.md: metadata table, per-section
    headings with embedded extracted-parameter tables, recommended-alternatives
    tables, tool insight blockquotes, horizontal rules.
    """
    today = date.today().isoformat()
    lines: list[str] = [
        "# 🔬 Protocol Assessment Report",
        "",
        "| Field | Value |",
        "|:---|:---|",
        f"| **Date** | {today} |",
        "| **Analysis type** | 3Rs alternative method mapping (DB-ALM) |",
    ]
    if study_summary.strip():
        lines.append(
            f"| **Input summary** | {_md_cell(study_summary.strip()[:2000])} |"
        )
    lines.extend(["", "---", ""])

    if not enriched_sections:
        lines.append(
            "*No in vivo, ex vivo, or in vitro tissue experiment blocks were extracted from the input.*"
        )
        lines.append("")

    for sec in enriched_sections:
        sid = sec.get("section_id", "—")
        dom = sec.get("domain", "—")
        nd = sec.get("normalized_domain", "")
        lines.append(f"## Section {_md_cell(sid)}: {_md_cell(dom)}")
        if nd and str(nd).strip() and str(nd).strip().lower() != str(dom).strip().lower():
            lines.append(f"**Mapped topic (DB-ALM):** *{_md_cell(nd)}*")
        lines.append("")
        lines.append(_format_section_parameters_markdown(sec))
        lines.append("### Recommended alternatives")
        lines.append("")

        hits = sec.get("catalogue_hits") or []
        if not hits:
            lines.append("*No catalogue methods matched this topic area.*")
            lines.append("")
            lines.append("---")
            lines.append("")
            continue

        lines.append(
            "| Method name | Validation (DB-ALM) | Regulatory authority | "
            "Endpoint coverage | Match score | Regulatory links |"
        )
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for h in hits:
            title = h.get("Title") or "—"
            vt = h.get("validation_tier") or "—"
            ra = h.get("regulatory_authority_tier", "—")
            ec = h.get("endpoint_coverage_tier", "—")
            score = h.get("match_score", "—")
            src = _regulatory_links_cell(h)
            vt_cell = _validation_cell_with_oecd(vt) if vt != "—" else "—"
            lines.append(
                f"| **{_md_cell(title)}** | {vt_cell} | {_md_cell(ra)} | "
                f"{_md_cell(ec)} | {_md_cell(score)} | {src} |"
            )

        lines.append("")
        best = hits[0]
        lines.append(
            "> **💡 Tool insight:** The strongest match here shows **"
            f"{_md_cell(best.get('regulatory_authority_tier'))}** regulatory standing "
            f"and **{_md_cell(best.get('endpoint_coverage_tier'))}** alignment with your "
            "stated endpoints. Prefer **high** authority and **full** endpoint coverage "
            "when briefing an ethics committee."
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Summary recommendation")
    lines.append("")
    n_seg = len(enriched_sections)
    has_alternatives = any(sec.get("catalogue_hits") for sec in enriched_sections)
    if has_alternatives:
        lines.append(
            f"This report lists up to **{n_seg}** protocol segment(s) with "
            "ranked DB-ALM alternatives. Use **high** regulatory authority and **full** "
            "endpoint matches first; consider **proxy** rows where a mechanistic rationale "
            "is documented."
        )
    else:
        lines.append(
            f"This report reflects **{n_seg}** extracted protocol segment(s), but "
            "**no DB-ALM catalogue matches** were returned for those topics. "
            "Try a clearer or fuller Materials and Methods excerpt, or search the "
            "DB-ALM catalogue directly for related methods."
        )
    lines.append("")

    return "\n".join(lines)

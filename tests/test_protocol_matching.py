"""Core parsing and matching invariants."""

from __future__ import annotations

import json

import pandas as pd

from method_finder.matching.protocol_matching import (
    compute_match_breakdown,
    parse_protocol_json,
    regulatory_authority_tier,
)


def test_parse_protocol_json_preferred_shape():
    raw = json.dumps(
        {
            "study_summary": "Summary text.",
            "experiments": [{"section_id": "1", "domain": "Acute Tox"}],
        }
    )
    sections, summary = parse_protocol_json(raw)
    assert summary == "Summary text."
    assert len(sections) == 1
    assert sections[0]["section_id"] == "1"


def test_parse_protocol_json_strips_fence():
    inner = '{"study_summary": "", "experiments": []}'
    raw = "```json\n" + inner + "\n```"
    sections, _ = parse_protocol_json(raw)
    assert sections == []


def test_compute_match_breakdown_signature():
    section = {"endpoints_measured": ["LD50"]}
    row = pd.Series(
        {
            "Title": "Test",
            "No.": "1",
            "validation_tier": "Validated (OECD/EURL-ECVAM #1)",
            "Regulatory  information": "",
            "Biological endpoints": ["lethal dose"],
        }
    )
    out = compute_match_breakdown(section, row)
    assert "match_score" in out
    assert out["regulatory_authority_tier"] in ("high", "medium", "low")


def test_regulatory_authority_tier_oecd_tg_in_title():
    row = pd.Series(
        {
            "Title": "Method OECD TG 123",
            "Regulatory  information": "",
            "validation_tier": "",
        }
    )
    pts, label = regulatory_authority_tier(row)
    assert pts == 3 and label == "high"

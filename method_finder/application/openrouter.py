"""OpenRouter POST flow: mock / plain LLM text / enriched JSON + report."""

from __future__ import annotations

import json
from typing import Any

import markdown

from method_finder.infrastructure.alm_catalogue import get_catalogue
from method_finder.infrastructure.openrouter_client import (
    DEFAULT_MODEL,
    complete_openrouter_extraction,
    mock_response,
)
from method_finder.matching.protocol_matching import (
    clamp_top_matches,
    enrich_protocol_with_catalogue,
    parse_protocol_json,
)
from method_finder.presentation.protocol_report import format_protocol_report_markdown

RUN_MODES: dict[str, str | None] = {
    "mock": None,
    "test": DEFAULT_MODEL,
    "production": "anthropic/claude-3.5-sonnet",
}


def process_openrouter_request(data: dict[str, Any] | None) -> tuple[str, int, Any]:
    """Return a (kind, http_status, payload) triple for the view layer to map to Flask."""
    try:
        return _process_openrouter_request(data)
    except RuntimeError as exc:
        return "error", 502, str(exc)
    except Exception as exc:
        return "error", 500, str(exc)


def _process_openrouter_request(data: dict[str, Any] | None) -> tuple[str, int, Any]:
    if data is None:
        return "error", 400, "Request body must be valid JSON"

    mode = data.get("model", "test")
    if mode not in RUN_MODES:
        mode = "test"

    if mode == "mock":
        try:
            md_source = mock_response(str(data.get("prompt", "")))
        except OSError as exc:
            return "error", 500, f"Could not load mock output: {exc}"
        html_body = markdown.markdown(
            md_source,
            extensions=[
                "markdown.extensions.tables",
                "markdown.extensions.nl2br",
            ],
        )
        return "html", 200, html_body

    if "prompt" not in data:
        return "error", 400, 'Missing "prompt" in JSON body'

    model_id = RUN_MODES[mode]
    assert model_id is not None
    response = complete_openrouter_extraction(data["prompt"], model=model_id)

    if not data.get("enrich_matches"):
        return "plain", 200, response

    try:
        df = get_catalogue()
    except Exception as exc:
        return "error", 503, f"DB-ALM catalogue is not available for matching: {exc}"

    try:
        sections, extracted_study_summary = parse_protocol_json(response)
    except (ValueError, json.JSONDecodeError) as exc:
        return "error", 502, f"Model output is not valid protocol JSON: {exc}"

    try:
        raw_n = data.get("max_catalogue_matches", 5)
        top_n = clamp_top_matches(int(raw_n) if raw_n is not None else 5)
    except (TypeError, ValueError):
        top_n = 5

    enriched = enrich_protocol_with_catalogue(
        sections, df, max_hits_per_section=top_n
    )

    study_for_report = (extracted_study_summary or "").strip()
    if not study_for_report:
        study_for_report = (data.get("prompt") or "").strip()[:800]

    report_md = format_protocol_report_markdown(
        enriched, study_summary=study_for_report
    )
    report_html = markdown.markdown(
        report_md,
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.nl2br",
        ],
    )

    return "json", 200, {
        "model_output": response,
        "study_summary": extracted_study_summary or None,
        "protocol_sections": enriched,
        "report_markdown": report_md,
        "report_html": report_html,
        "max_catalogue_matches": top_n,
    }

"""Flask application factory and HTTP routes."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

from method_finder.application.openrouter import process_openrouter_request
from method_finder.application.sample_inputs import load_sample_input_records
from method_finder.infrastructure.alm_catalogue import get_catalogue, load_catalogue


def create_app() -> Flask:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    try:
        load_catalogue()
        print(f"DB-ALM catalogue: loaded {len(get_catalogue())} methods into memory.")
    except Exception as exc:
        print(f"Warning: DB-ALM catalogue not loaded ({exc})")

    app = Flask(
        __name__,
        static_folder=str(repo_root / "static"),
        template_folder=str(repo_root / "templates"),
    )

    @app.route("/openrouter", methods=["POST"])
    def open_router_post() -> tuple[Response, int] | Response:
        kind, status, payload = process_openrouter_request(request.get_json(silent=True))
        if kind == "error":
            return jsonify({"error": payload}), status
        if kind == "html":
            return Response(payload, mimetype="text/html; charset=utf-8")
        if kind == "plain":
            return Response(payload, mimetype="text/plain; charset=utf-8")
        return jsonify(payload)

    @app.route("/api/sample-inputs")
    def sample_inputs_api():
        return jsonify(load_sample_input_records())

    @app.route("/")
    def index():
        return render_template("index.html")

    return app

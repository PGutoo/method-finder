import json
import ast
from pathlib import Path

import markdown
from flask import Flask, Response, request, render_template
from service.openrouter_service import DEFAULT_MODEL, mock_response, open_router

_APP_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    static_folder=str(_APP_DIR / "static"),
    template_folder=str(_APP_DIR / "templates"),
)

RUN_MODES = {
    "mock": None,
    "test": DEFAULT_MODEL,
    "production": "anthropic/claude-3.5-sonnet",
}


@app.route('/openrouter', methods=['POST'])
def open_router_test():
    try:
        data = request.json or {}
        mode = data.get("model", "test")
        if mode not in RUN_MODES:
            mode = "test"
        if mode == "mock":
            md_source = mock_response(data.get("prompt", ""))
            html_body = markdown.markdown(
                md_source,
                extensions=[
                    "markdown.extensions.tables",
                    "markdown.extensions.nl2br",
                ],
            )
            return Response(html_body, mimetype="text/html; charset=utf-8")
        response = open_router(data["prompt"], model=RUN_MODES[mode])
        return Response(response, mimetype="text/plain; charset=utf-8")
    except Exception as e:
        print(e)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

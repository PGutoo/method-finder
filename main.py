"""WSGI entrypoint for Vercel and local ``python main.py``."""

from method_finder.webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

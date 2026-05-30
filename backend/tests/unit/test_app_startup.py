"""Smoke tests that catch production-only dependency and import failures."""

from pathlib import Path


def test_production_requirements_include_runtime_dependencies():
    """requirements-dev.txt adds httpx for tests; production uses requirements.txt only."""
    text = Path(__file__).resolve().parents[2].joinpath("requirements.txt").read_text(encoding="utf-8")
    lowered = text.lower()
    for package in ("babel", "httpx", "fastapi", "sqlalchemy"):
        assert package in lowered, f"{package} must be listed in backend/requirements.txt"


def test_app_imports_with_production_requirements_only():
    """Importing the FastAPI app must succeed with the same deps as the Docker image."""
    from app.main import app

    assert app.title
    assert app.version

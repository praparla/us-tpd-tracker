"""Shared fixtures for tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture
def deals_json_path() -> Path:
    return DATA_DIR / "deals.json"


@pytest.fixture
def sample_json_path() -> Path:
    return DATA_DIR / "deals.sample.json"


@pytest.fixture
def deals_data(deals_json_path: Path) -> dict:
    """Load and return parsed deals.json."""
    assert deals_json_path.exists(), f"deals.json not found at {deals_json_path}"
    return json.loads(deals_json_path.read_text())


@pytest.fixture
def sample_data(sample_json_path: Path) -> dict:
    """Load and return parsed deals.sample.json."""
    assert sample_json_path.exists(), f"deals.sample.json not found at {sample_json_path}"
    return json.loads(sample_json_path.read_text())

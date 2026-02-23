"""Unit tests for pipeline configuration.

Validates watchlist structure, keywords, source definitions, and constants.
Run with: PYTHONPATH=. python3 -m pytest tests/test_config.py -v
"""
from __future__ import annotations

from pathlib import Path

from pipeline.config import (
    BACKOFF_START_SECONDS,
    COUNTRY_WATCHLIST,
    DEAL_KEYWORDS,
    DEFAULT_MODEL,
    MAX_INPUT_TOKENS,
    MAX_RETRIES,
    PREFILTER_KEYWORDS,
    PREMIUM_MODEL,
    PROJECT_ROOT,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    SCRAPER_VERSION,
    SOURCES,
    TECH_KEYWORDS,
    USER_AGENT,
)


class TestCountryWatchlist:
    """Validate COUNTRY_WATCHLIST structure."""

    def test_three_countries(self) -> None:
        assert len(COUNTRY_WATCHLIST) == 3

    def test_expected_keys(self) -> None:
        assert set(COUNTRY_WATCHLIST.keys()) == {"UK", "Japan", "South Korea"}

    def test_each_has_required_fields(self) -> None:
        for key, info in COUNTRY_WATCHLIST.items():
            assert "names" in info, f"{key} missing 'names'"
            assert "code" in info, f"{key} missing 'code'"
            assert isinstance(info["names"], list), f"{key} 'names' should be a list"
            assert len(info["names"]) > 0, f"{key} has empty names list"

    def test_iso_codes(self) -> None:
        codes = {info["code"] for info in COUNTRY_WATCHLIST.values()}
        assert codes == {"GBR", "JPN", "KOR"}

    def test_names_are_strings(self) -> None:
        for key, info in COUNTRY_WATCHLIST.items():
            for name in info["names"]:
                assert isinstance(name, str), f"{key} has non-string name: {name}"

    def test_primary_names_present(self) -> None:
        uk_names = [n.lower() for n in COUNTRY_WATCHLIST["UK"]["names"]]
        assert "united kingdom" in uk_names
        assert "uk" in uk_names

        jpn_names = [n.lower() for n in COUNTRY_WATCHLIST["Japan"]["names"]]
        assert "japan" in jpn_names

        kor_names = [n.lower() for n in COUNTRY_WATCHLIST["South Korea"]["names"]]
        assert "south korea" in kor_names
        assert "korea" in kor_names


class TestKeywords:
    """Validate keyword lists."""

    def test_tech_keywords_non_empty(self) -> None:
        assert len(TECH_KEYWORDS) > 0

    def test_deal_keywords_non_empty(self) -> None:
        assert len(DEAL_KEYWORDS) > 0

    def test_prefilter_is_union(self) -> None:
        assert set(PREFILTER_KEYWORDS) == set(TECH_KEYWORDS + DEAL_KEYWORDS)

    def test_core_tech_keywords_present(self) -> None:
        kw_lower = [k.lower() for k in TECH_KEYWORDS]
        assert "ai" in kw_lower or "artificial intelligence" in kw_lower
        assert "semiconductor" in kw_lower
        assert "quantum" in kw_lower

    def test_core_deal_keywords_present(self) -> None:
        kw_lower = [k.lower() for k in DEAL_KEYWORDS]
        assert "prosperity" in kw_lower
        assert "agreement" in kw_lower
        assert "investment" in kw_lower


class TestSources:
    """Validate data source configuration."""

    def test_four_sources(self) -> None:
        assert len(SOURCES) == 4

    def test_expected_source_names(self) -> None:
        assert set(SOURCES.keys()) == {"federal_register", "whitehouse", "commerce", "ustr"}

    def test_federal_register_has_api_base(self) -> None:
        assert "api_base" in SOURCES["federal_register"]
        assert "federalregister.gov" in SOURCES["federal_register"]["api_base"]

    def test_whitehouse_has_endpoints(self) -> None:
        assert "fact_sheets" in SOURCES["whitehouse"]
        assert "articles" in SOURCES["whitehouse"]

    def test_all_sources_have_max_pages_or_per_page(self) -> None:
        for name, config in SOURCES.items():
            has_pagination = "max_pages" in config or "per_page" in config
            assert has_pagination, f"{name} missing pagination config"


class TestNetworkConstants:
    """Validate network-related constants."""

    def test_rate_limit_positive(self) -> None:
        assert REQUEST_DELAY_SECONDS > 0

    def test_backoff_reasonable(self) -> None:
        assert BACKOFF_START_SECONDS >= 5

    def test_retries_positive(self) -> None:
        assert MAX_RETRIES >= 1

    def test_timeout_positive(self) -> None:
        assert REQUEST_TIMEOUT_SECONDS > 0

    def test_user_agent_set(self) -> None:
        assert "us-tpd-tracker" in USER_AGENT


class TestModelConfig:
    """Validate AI model configuration."""

    def test_default_model_is_haiku(self) -> None:
        assert "haiku" in DEFAULT_MODEL

    def test_premium_model_is_opus(self) -> None:
        assert "opus" in PREMIUM_MODEL

    def test_max_input_tokens_reasonable(self) -> None:
        assert 100 <= MAX_INPUT_TOKENS <= 4000

    def test_scraper_version_format(self) -> None:
        parts = SCRAPER_VERSION.split(".")
        assert len(parts) == 3
        for part in parts:
            int(part)  # should not raise


class TestPaths:
    """Validate path configuration."""

    def test_project_root_exists(self) -> None:
        assert PROJECT_ROOT.exists()

    def test_project_root_has_pipeline(self) -> None:
        assert (PROJECT_ROOT / "pipeline").is_dir()

    def test_project_root_has_data(self) -> None:
        assert (PROJECT_ROOT / "data").is_dir()

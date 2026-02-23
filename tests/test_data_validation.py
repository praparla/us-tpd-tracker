"""Validate deals.json and deals.sample.json against schema and business rules.

Run with: PYTHONPATH=. python3 -m pytest tests/ -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.config import COUNTRY_WATCHLIST
from pipeline.models import DealsOutput, DealStatus, DealType


# ── Schema validation ────────────────────────────────────────────────

class TestDealsJsonSchema:
    """Validate deals.json conforms to the Pydantic schema."""

    def test_deals_json_exists(self, deals_json_path: Path) -> None:
        assert deals_json_path.exists(), "data/deals.json must exist"

    def test_deals_json_is_valid_json(self, deals_json_path: Path) -> None:
        data = json.loads(deals_json_path.read_text())
        assert isinstance(data, dict)

    def test_deals_json_validates_against_schema(self, deals_data: dict) -> None:
        output = DealsOutput.model_validate(deals_data)
        assert output.meta is not None
        assert isinstance(output.items, list)

    def test_has_items(self, deals_data: dict) -> None:
        assert len(deals_data["items"]) > 0, "deals.json should have at least one deal"


class TestSampleJsonSchema:
    """Validate deals.sample.json conforms to the Pydantic schema."""

    def test_sample_json_exists(self, sample_json_path: Path) -> None:
        assert sample_json_path.exists(), "data/deals.sample.json must exist"

    def test_sample_json_validates_against_schema(self, sample_data: dict) -> None:
        output = DealsOutput.model_validate(sample_data)
        assert output.meta is not None
        assert len(output.items) > 0


# ── Meta field validation ────────────────────────────────────────────

class TestMetaFields:
    """Validate meta section of deals.json."""

    def test_generated_at_present(self, deals_data: dict) -> None:
        assert deals_data["meta"]["generated_at"], "generated_at must be set"

    def test_scraper_version_present(self, deals_data: dict) -> None:
        assert deals_data["meta"]["scraper_version"], "scraper_version must be set"

    def test_countries_tracked(self, deals_data: dict) -> None:
        countries = deals_data["meta"].get("countries_tracked", [])
        assert len(countries) > 0, "Should track at least one country"
        valid_codes = {info["code"] for info in COUNTRY_WATCHLIST.values()}
        for code in countries:
            assert code in valid_codes, f"Unknown country code: {code}"

    def test_sources_scraped(self, deals_data: dict) -> None:
        sources = deals_data["meta"].get("sources_scraped", [])
        valid_sources = {"federal_register", "whitehouse", "commerce", "ustr"}
        for source in sources:
            assert source in valid_sources, f"Unknown source: {source}"


# ── Deal field validation ────────────────────────────────────────────

class TestDealFields:
    """Validate individual deal items."""

    def test_all_deals_have_required_fields(self, deals_data: dict) -> None:
        required = {"id", "title", "summary", "type", "status", "country", "date", "source_url"}
        for deal in deals_data["items"]:
            missing = required - set(deal.keys())
            assert not missing, f"Deal {deal.get('id', '?')} missing fields: {missing}"

    def test_no_duplicate_ids(self, deals_data: dict) -> None:
        ids = [deal["id"] for deal in deals_data["items"]]
        duplicates = [x for x in ids if ids.count(x) > 1]
        assert not duplicates, f"Duplicate deal IDs: {set(duplicates)}"

    def test_valid_deal_types(self, deals_data: dict) -> None:
        valid_types = {t.value for t in DealType}
        for deal in deals_data["items"]:
            assert deal["type"] in valid_types, (
                f"Deal {deal['id']} has invalid type: {deal['type']}"
            )

    def test_valid_deal_statuses(self, deals_data: dict) -> None:
        valid_statuses = {s.value for s in DealStatus}
        for deal in deals_data["items"]:
            assert deal["status"] in valid_statuses, (
                f"Deal {deal['id']} has invalid status: {deal['status']}"
            )

    def test_deal_values_non_negative(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            value = deal.get("deal_value_usd")
            if value is not None:
                assert value >= 0, (
                    f"Deal {deal['id']} has negative value: {value}"
                )

    def test_dates_are_valid_format(self, deals_data: dict) -> None:
        import re
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for deal in deals_data["items"]:
            assert date_pattern.match(deal["date"]), (
                f"Deal {deal['id']} has invalid date format: {deal['date']}"
            )


# ── Hierarchical structure validation ────────────────────────────────

class TestHierarchy:
    """Validate parent-child deal relationships."""

    def test_parent_deals_exist(self, deals_data: dict) -> None:
        parents = [d for d in deals_data["items"] if d.get("parent_id") is None]
        assert len(parents) > 0, "Should have at least one parent TPD"

    def test_child_deals_reference_valid_parents(self, deals_data: dict) -> None:
        parent_ids = {d["id"] for d in deals_data["items"] if d.get("parent_id") is None}
        for deal in deals_data["items"]:
            pid = deal.get("parent_id")
            if pid is not None:
                assert pid in parent_ids, (
                    f"Child deal {deal['id']} references non-existent parent: {pid}"
                )

    def test_parent_deals_have_no_parent(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            if deal.get("parent_id") is None:
                # Parent deals should be TRADE type (framework agreements)
                assert deal["type"] == "TRADE", (
                    f"Parent deal {deal['id']} should be type TRADE, got {deal['type']}"
                )

    def test_child_deals_have_same_country_as_parent(self, deals_data: dict) -> None:
        parent_countries = {
            d["id"]: d["country"]
            for d in deals_data["items"]
            if d.get("parent_id") is None
        }
        for deal in deals_data["items"]:
            pid = deal.get("parent_id")
            if pid is not None and pid in parent_countries:
                assert deal["country"] == parent_countries[pid], (
                    f"Child {deal['id']} country ({deal['country']}) "
                    f"doesn't match parent {pid} country ({parent_countries[pid]})"
                )


# ── Country validation ───────────────────────────────────────────────

class TestCountries:
    """Validate country codes in deals."""

    def test_country_codes_are_valid(self, deals_data: dict) -> None:
        valid_codes = {info["code"] for info in COUNTRY_WATCHLIST.values()}
        for deal in deals_data["items"]:
            assert deal["country"] in valid_codes, (
                f"Deal {deal['id']} has unknown country code: {deal['country']}"
            )

    def test_all_tracked_countries_have_deals(self, deals_data: dict) -> None:
        deal_countries = {d["country"] for d in deals_data["items"]}
        tracked = set(deals_data["meta"].get("countries_tracked", []))
        for code in tracked:
            assert code in deal_countries, (
                f"Country {code} is tracked but has no deals"
            )


# ── Content quality checks ───────────────────────────────────────────

class TestContentQuality:
    """Basic content quality checks."""

    def test_titles_not_empty(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            assert deal["title"].strip(), f"Deal {deal['id']} has empty title"

    def test_summaries_not_empty(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            assert deal["summary"].strip(), f"Deal {deal['id']} has empty summary"

    def test_source_urls_are_urls(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            url = deal["source_url"]
            assert url.startswith("http"), (
                f"Deal {deal['id']} source_url doesn't look like a URL: {url}"
            )

    def test_parties_present(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            assert len(deal.get("parties", [])) > 0, (
                f"Deal {deal['id']} has no parties listed"
            )


# ── Scraper filter tests ─────────────────────────────────────────────

class TestScraperFilters:
    """Test the title matching filter used by scrapers."""

    def test_matches_prosperity(self) -> None:
        from pipeline.scrapers.base import title_matches_watchlist
        assert title_matches_watchlist("Technology Prosperity Deal")

    def test_matches_country_plus_keyword(self) -> None:
        from pipeline.scrapers.base import title_matches_watchlist
        assert title_matches_watchlist("Japan bilateral technology agreement")
        assert title_matches_watchlist("UK trade deal partnership")
        assert title_matches_watchlist("South Korea semiconductor investment")

    def test_rejects_unrelated(self) -> None:
        from pipeline.scrapers.base import title_matches_watchlist
        assert not title_matches_watchlist("Random news article about weather")
        assert not title_matches_watchlist("US domestic policy update")

    def test_country_filter(self) -> None:
        from pipeline.scrapers.base import title_matches_watchlist
        assert title_matches_watchlist("Japan technology deal", country_filter="Japan")
        assert not title_matches_watchlist("Japan technology deal", country_filter="UK")

    def test_matches_broader_tpd_phrases(self) -> None:
        from pipeline.scrapers.base import title_matches_watchlist
        assert title_matches_watchlist(
            "President Trump Brings Home Billion Dollar Deals During State Visit to Korea"
        )
        assert title_matches_watchlist("US-Japan Summit Joint Statement")

"""Unit tests for the classifier module (no API calls).

Tests passes_prefilter(), truncate_text(), _country_name_from_code(),
and Classifier._parse_result() with mock data.
Run with: PYTHONPATH=. python3 -m pytest tests/test_classifier.py -v
"""
from __future__ import annotations

import pytest

from pipeline.classifier import (
    Classifier,
    _country_name_from_code,
    passes_prefilter,
    truncate_text,
)
from pipeline.models import RawDeal


# ── Pre-filter tests ────────────────────────────────────────────────

class TestPassesPrefilter:
    """Test the keyword pre-filter."""

    def test_accepts_tech_keywords_in_title(self) -> None:
        raw = RawDeal(title="Japan AI Partnership", source_url="https://example.com")
        assert passes_prefilter(raw)

    def test_accepts_deal_keywords_in_title(self) -> None:
        raw = RawDeal(title="US-Korea Trade Agreement", source_url="https://example.com")
        assert passes_prefilter(raw)

    def test_accepts_keywords_in_snippet(self) -> None:
        raw = RawDeal(
            title="Press Release",
            source_url="https://example.com",
            snippet="bilateral technology investment in semiconductors",
        )
        assert passes_prefilter(raw)

    def test_rejects_unrelated(self) -> None:
        raw = RawDeal(
            title="Weather Update",
            source_url="https://example.com",
            snippet="sunny skies expected tomorrow",
        )
        assert not passes_prefilter(raw)

    def test_case_insensitive(self) -> None:
        raw = RawDeal(title="QUANTUM COMPUTING AGREEMENT", source_url="https://example.com")
        assert passes_prefilter(raw)

    def test_prosperity_keyword(self) -> None:
        raw = RawDeal(title="Technology Prosperity Deal", source_url="https://example.com")
        assert passes_prefilter(raw)

    def test_semiconductor_keyword(self) -> None:
        raw = RawDeal(title="Korea semiconductor investment", source_url="https://example.com")
        assert passes_prefilter(raw)


# ── Truncation tests ───────────────────────────────────────────────

class TestTruncateText:
    """Test smart text truncation."""

    def test_short_text_unchanged(self) -> None:
        text = "Short text under the limit."
        assert truncate_text(text, max_tokens=100) == text

    def test_long_text_truncated(self) -> None:
        words = ["word"] * 2000
        text = " ".join(words)
        result = truncate_text(text, max_tokens=800)
        assert len(result.split()) <= 800

    def test_preserves_dollar_lines(self) -> None:
        lines = ["Introduction paragraph " * 20]
        lines.extend(["filler line"] * 10)
        lines.append("Korean Air: $36.2 billion Boeing purchase")
        lines.append("AWS: $5 billion cloud investment")
        lines.extend(["more filler " * 50] * 20)
        text = "\n".join(lines)
        result = truncate_text(text, max_tokens=600)
        assert "$36.2 billion" in result or "$5 billion" in result

    def test_preserves_bullet_points(self) -> None:
        lines = ["First section " * 50]
        lines.extend(["padding"] * 10)
        lines.append("• $10 billion investment in US facilities")
        lines.append("- $5 billion semiconductor plant")
        lines.extend(["more padding " * 50] * 20)
        text = "\n".join(lines)
        result = truncate_text(text, max_tokens=600)
        assert "billion" in result

    def test_exact_boundary(self) -> None:
        words = ["word"] * 800
        text = " ".join(words)
        result = truncate_text(text, max_tokens=800)
        assert result == text


# ── Country name helper tests ──────────────────────────────────────

class TestCountryNameFromCode:
    """Test _country_name_from_code helper."""

    def test_gbr(self) -> None:
        name = _country_name_from_code("GBR")
        assert "Kingdom" in name or "UK" in name

    def test_jpn(self) -> None:
        assert _country_name_from_code("JPN") == "Japan"

    def test_kor(self) -> None:
        name = _country_name_from_code("KOR")
        assert "Korea" in name

    def test_unknown_returns_code(self) -> None:
        assert _country_name_from_code("XYZ") == "XYZ"


# ── Classifier._parse_result tests ────────────────────────────────

class TestParseResult:
    """Test converting API-style results into Deal objects."""

    @pytest.fixture
    def classifier(self) -> Classifier:
        return Classifier(prefilter_enabled=False, truncation_enabled=False)

    @pytest.fixture
    def sample_raw(self) -> RawDeal:
        return RawDeal(
            title="US-Korea TPD",
            source_url="https://example.com/kor",
            raw_date="2025-10-29",
            source_name="whitehouse",
        )

    def test_non_tpd_returns_empty(self, classifier: Classifier, sample_raw: RawDeal) -> None:
        parent, children = classifier._parse_result(
            {"is_tpd": False}, sample_raw, "tpd-kor", 2025
        )
        assert parent is None
        assert children == []

    def test_tpd_returns_parent(self, classifier: Classifier, sample_raw: RawDeal) -> None:
        data = {
            "is_tpd": True,
            "parent": {
                "title": "US-Korea Technology Prosperity Deal",
                "summary": "Bilateral tech partnership",
                "country_code": "KOR",
                "date_signed": "2025-10-29",
                "signatories": ["President Trump"],
                "sectors": ["AI", "6G"],
                "total_value_usd": 75000000000,
                "status": "SIGNED",
            },
            "children": [],
        }
        parent, children = classifier._parse_result(data, sample_raw, "tpd-kor", 2025)
        assert parent is not None
        assert parent.country == "KOR"
        assert parent.type.value == "TRADE"
        assert children == []

    def test_tpd_returns_children(self, classifier: Classifier, sample_raw: RawDeal) -> None:
        data = {
            "is_tpd": True,
            "parent": {
                "title": "Test",
                "summary": "Test",
                "country_code": "KOR",
                "status": "SIGNED",
            },
            "children": [
                {
                    "title": "Korean Air Boeing Purchase",
                    "summary": "$36.2B aircraft deal",
                    "parties": ["Korean Air", "Boeing"],
                    "deal_value_usd": 36200000000,
                    "sector": "Aviation & Defense",
                    "commitment_details": "103 aircraft",
                    "status": "COMMITTED",
                },
                {
                    "title": "AWS Cloud Investment",
                    "summary": "$5B cloud",
                    "parties": ["AWS"],
                    "deal_value_usd": 5000000000,
                    "sector": "Technology & Cloud",
                    "status": "COMMITTED",
                },
            ],
        }
        parent, children = classifier._parse_result(data, sample_raw, "tpd-kor", 2025)
        assert len(children) == 2
        assert children[0].deal_value_usd == 36200000000
        assert children[0].parent_id is not None
        assert children[1].parties == ["AWS"]

    def test_child_ids_sequential(self, classifier: Classifier, sample_raw: RawDeal) -> None:
        data = {
            "is_tpd": True,
            "parent": {"title": "T", "summary": "S", "country_code": "KOR", "status": "SIGNED"},
            "children": [
                {"title": "A", "summary": "A", "status": "COMMITTED"},
                {"title": "B", "summary": "B", "status": "COMMITTED"},
            ],
        }
        parent, children = classifier._parse_result(data, sample_raw, "tpd-kor", 2025)
        assert children[0].id.endswith("-001")
        assert children[1].id.endswith("-002")


# ── Cost estimation tests ──────────────────────────────────────────

class TestEstimateCost:
    """Test cost estimation logic."""

    def test_zero_calls_zero_cost(self) -> None:
        c = Classifier()
        c.stats.new_api_calls = 0
        assert c.estimate_cost() == 0.0

    def test_haiku_cheaper_than_opus(self) -> None:
        haiku = Classifier(model="claude-3-5-haiku-20241022")
        haiku.stats.new_api_calls = 10
        haiku_cost = haiku.estimate_cost()

        opus = Classifier(model="claude-opus-4-5-20250220")
        opus.stats.new_api_calls = 10
        opus_cost = opus.estimate_cost()

        assert haiku_cost < opus_cost

    def test_batch_mode_halves_cost(self) -> None:
        normal = Classifier()
        normal.stats.new_api_calls = 10
        normal_cost = normal.estimate_cost()

        batch = Classifier(batch_mode=True)
        batch.stats.new_api_calls = 10
        batch_cost = batch.estimate_cost()

        assert batch_cost == pytest.approx(normal_cost * 0.5)

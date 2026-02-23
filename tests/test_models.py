"""Unit tests for Pydantic models.

Tests Deal, Meta, DealsOutput, enums, and validation constraints.
Run with: PYTHONPATH=. python3 -m pytest tests/test_models.py -v
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from pipeline.models import (
    CostOptimization,
    Deal,
    DealStatus,
    DealType,
    DealsOutput,
    ErrorRecord,
    Meta,
    RawDeal,
    SourceDocument,
)


class TestDealType:
    """Test DealType enum."""

    def test_valid_values(self) -> None:
        assert DealType.GOVERNMENT == "GOVERNMENT"
        assert DealType.BUSINESS == "BUSINESS"
        assert DealType.TRADE == "TRADE"

    def test_all_three_types(self) -> None:
        assert len(DealType) == 3


class TestDealStatus:
    """Test DealStatus enum."""

    def test_valid_values(self) -> None:
        assert DealStatus.ACTIVE == "ACTIVE"
        assert DealStatus.PENDING == "PENDING"
        assert DealStatus.COMPLETED == "COMPLETED"
        assert DealStatus.CANCELLED == "CANCELLED"
        assert DealStatus.REPORTED == "REPORTED"

    def test_all_five_statuses(self) -> None:
        assert len(DealStatus) == 5


class TestSourceDocument:
    """Test SourceDocument model."""

    def test_valid(self) -> None:
        doc = SourceDocument(label="Fact Sheet", url="https://example.com")
        assert doc.label == "Fact Sheet"
        assert doc.url == "https://example.com"

    def test_requires_label_and_url(self) -> None:
        with pytest.raises(ValidationError):
            SourceDocument(label="test")  # type: ignore
        with pytest.raises(ValidationError):
            SourceDocument(url="https://example.com")  # type: ignore


class TestRawDeal:
    """Test RawDeal model."""

    def test_minimal(self) -> None:
        raw = RawDeal(title="Test", source_url="https://example.com")
        assert raw.title == "Test"
        assert raw.source_id == ""
        assert raw.snippet == ""

    def test_full(self) -> None:
        raw = RawDeal(
            title="Japan TPD",
            source_url="https://example.com",
            source_id="WH-123",
            snippet="Technology partnership...",
            raw_date="2025-10-28",
            source_name="whitehouse",
        )
        assert raw.source_name == "whitehouse"


class TestDeal:
    """Test Deal model."""

    def test_minimal_parent(self) -> None:
        deal = Deal(
            id="tpd-jpn-2025",
            source_url="https://example.com",
            title="US-Japan TPD",
            summary="Test",
            type=DealType.TRADE,
            status=DealStatus.ACTIVE,
            date="2025-10-28",
        )
        assert deal.parent_id is None
        assert deal.deal_value_usd is None
        assert deal.parties == []

    def test_child_deal(self) -> None:
        deal = Deal(
            id="tpd-jpn-2025-001",
            parent_id="tpd-jpn-2025",
            source_url="https://example.com",
            title="Korean Air Boeing Purchase",
            summary="Test",
            type=DealType.BUSINESS,
            status=DealStatus.ACTIVE,
            date="2025-10-29",
            deal_value_usd=36200000000,
            parties=["Korean Air", "Boeing"],
        )
        assert deal.parent_id == "tpd-jpn-2025"
        assert deal.deal_value_usd == 36200000000

    def test_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Deal(
                id="test",
                source_url="https://example.com",
                title="Test",
                summary="Test",
                type="INVALID",  # type: ignore
                status=DealStatus.ACTIVE,
                date="2025-01-01",
            )

    def test_invalid_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Deal(
                id="test",
                source_url="https://example.com",
                title="Test",
                summary="Test",
                type=DealType.TRADE,
                status="INVALID",  # type: ignore
                date="2025-01-01",
            )

    def test_default_country(self) -> None:
        deal = Deal(
            id="test",
            source_url="https://example.com",
            title="Test",
            summary="Test",
            type=DealType.TRADE,
            status=DealStatus.ACTIVE,
            date="2025-01-01",
        )
        assert deal.country == "USA"


class TestMeta:
    """Test Meta model."""

    def test_minimal(self) -> None:
        meta = Meta(generated_at="2025-01-01T00:00:00Z")
        assert meta.deals_scanned == 0
        assert meta.max_items_cap is None
        assert meta.errors == []

    def test_full(self) -> None:
        meta = Meta(
            generated_at="2025-01-01T00:00:00Z",
            deals_scanned=100,
            deals_processed=42,
            max_items_cap=50,
            countries_tracked=["GBR", "JPN", "KOR"],
            sources_scraped=["whitehouse", "federal_register"],
        )
        assert meta.deals_processed == 42
        assert len(meta.countries_tracked) == 3


class TestCostOptimization:
    """Test CostOptimization model."""

    def test_defaults(self) -> None:
        cost = CostOptimization()
        assert cost.prefilter_enabled is True
        assert cost.batch_mode is False
        assert cost.estimated_cost_usd == 0.0

    def test_custom(self) -> None:
        cost = CostOptimization(
            model_used="claude-opus-4-5-20250220",
            new_api_calls=10,
            estimated_cost_usd=0.30,
        )
        assert cost.model_used == "claude-opus-4-5-20250220"


class TestDealsOutput:
    """Test DealsOutput top-level model."""

    def test_empty_items(self) -> None:
        output = DealsOutput(meta=Meta(generated_at="2025-01-01T00:00:00Z"))
        assert output.items == []

    def test_with_items(self) -> None:
        deal = Deal(
            id="test",
            source_url="https://example.com",
            title="Test",
            summary="Test",
            type=DealType.TRADE,
            status=DealStatus.ACTIVE,
            date="2025-01-01",
        )
        output = DealsOutput(
            meta=Meta(generated_at="2025-01-01T00:00:00Z"),
            items=[deal],
        )
        assert len(output.items) == 1


class TestErrorRecord:
    """Test ErrorRecord model."""

    def test_valid(self) -> None:
        err = ErrorRecord(source="https://ustr.gov/broken", error="404 Not Found")
        assert "404" in err.error

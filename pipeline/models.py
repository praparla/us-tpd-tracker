"""Pydantic v2 models for the US Tech Prosperity Deal Tracker.

Defines the data contract for pipeline output (data/deals.json).
Hierarchical model: parent TPDs contain child corporate commitments.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class DealType(str, Enum):
    GOVERNMENT = "GOVERNMENT"
    BUSINESS = "BUSINESS"
    TRADE = "TRADE"


class DealStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REPORTED = "REPORTED"


class SourceDocument(BaseModel):
    """A reference to an original source document (fact sheet, announcement, etc.)."""
    label: str
    url: str


class RawDeal(BaseModel):
    """Unclassified deal candidate from a scraper."""
    title: str
    source_url: str
    source_id: str = ""
    snippet: str = ""
    raw_date: str = ""
    source_name: str = ""  # e.g., "whitehouse", "federal_register"


class Deal(BaseModel):
    """Classified deal — the final output item.

    If parent_id is null, this is a top-level TPD framework deal.
    If parent_id is set, this is a child corporate commitment.
    """
    id: str
    parent_id: Optional[str] = None
    source_id: str = ""
    source_url: str
    title: str
    summary: str
    type: DealType
    status: DealStatus
    parties: List[str] = Field(default_factory=list)
    deal_value_usd: Optional[int] = None
    country: str = "USA"
    date: str  # YYYY-MM-DD
    date_signed: Optional[str] = None  # YYYY-MM-DD, for framework deals
    tags: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)
    signatories: List[str] = Field(default_factory=list)
    source_documents: List[SourceDocument] = Field(default_factory=list)
    commitment_details: Optional[str] = None  # for child commitments


class ErrorRecord(BaseModel):
    source: str
    error: str


class CostOptimization(BaseModel):
    prefilter_enabled: bool = True
    prefilter_skipped: int = 0
    truncation_enabled: bool = True
    model_used: str = "claude-3-5-haiku-20241022"
    cache_hits: int = 0
    new_api_calls: int = 0
    batch_mode: bool = False
    estimated_cost_usd: float = 0.0


class Meta(BaseModel):
    generated_at: str  # ISO 8601
    deals_scanned: int = 0
    deals_processed: int = 0
    max_items_cap: Optional[int] = None
    date_range_start: str = ""
    date_range_end: str = ""
    scraper_version: str = "1.0.0"
    countries_tracked: List[str] = Field(default_factory=list)
    sources_scraped: List[str] = Field(default_factory=list)
    cost_optimization: CostOptimization = Field(default_factory=CostOptimization)
    errors: List[ErrorRecord] = Field(default_factory=list)


class DealsOutput(BaseModel):
    """Top-level output shape for data/deals.json."""
    meta: Meta
    items: List[Deal] = Field(default_factory=list)

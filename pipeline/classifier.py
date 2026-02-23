"""AI classification engine for extracting structured deal data.

Uses Anthropic Claude API with a 5-layer cost optimization pipeline:
  Layer 1: Pre-filter (keyword matching — zero tokens, zero cost)
  Layer 2: Truncation (cap input at ~800 tokens — reduces per-call cost)
  Layer 3: Model selection (haiku default — cheapest model)
  Layer 4: Caching (content hash — re-runs are free)
  Layer 5: Batch API (opt-in — 50% discount, async)

Single API call per page extracts BOTH parent TPD info AND child commitments,
minimizing total API calls.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import List, Optional

from pydantic import ValidationError

from pipeline.cache import (
    clear_cache,
    content_hash,
    get_cached_classification,
    save_cached_classification,
)
from pipeline.config import (
    CLASSIFICATION_CACHE_DIR,
    COUNTRY_WATCHLIST,
    DEFAULT_MODEL,
    MAX_INPUT_TOKENS,
    PREFILTER_KEYWORDS,
    PREMIUM_MODEL,
)
from pipeline.models import CostOptimization, Deal, DealStatus, DealType, RawDeal, SourceDocument

logger = logging.getLogger(__name__)


# === Layer 1: Pre-filter ===

def passes_prefilter(raw: RawDeal) -> bool:
    """Keyword-based pre-filter. Returns True if the deal looks relevant.

    This is the cheapest possible check — pure string matching, no AI.
    Skips pages that clearly aren't about tech deals.
    """
    text = f"{raw.title} {raw.snippet}".lower()
    for kw in PREFILTER_KEYWORDS:
        if kw.lower() in text:
            return True
    logger.debug("Pre-filter REJECTED: %s", raw.title[:60])
    return False


# === Layer 2: Truncation ===

def truncate_text(text: str, max_tokens: int = MAX_INPUT_TOKENS) -> str:
    """Smart truncation: keep beginning + key sections.

    Targets ~800 tokens (approx 1 token per word).
    Preserves first section (usually the key summary) and any bullet points
    (often contain deal details like dollar values and company names).
    """
    words = text.split()
    if len(words) <= max_tokens:
        return text

    # Strategy: keep first 500 words + scan for bullet-point lines
    first_chunk = " ".join(words[:500])

    # Find lines that look like deal details (contain $, numbers, company-like patterns)
    lines = text.split("\n")
    detail_lines = []
    for line in lines[5:]:  # Skip first few lines (already in first_chunk)
        stripped = line.strip()
        if any(marker in stripped for marker in ["$", "billion", "million", "—", "•", "-"]):
            if len(stripped) > 20:
                detail_lines.append(stripped)

    # Combine, staying under token budget
    detail_text = "\n".join(detail_lines[:20])  # Cap at 20 detail lines
    combined = first_chunk + "\n\n---\n\n" + detail_text
    combined_words = combined.split()
    if len(combined_words) > max_tokens:
        combined = " ".join(combined_words[:max_tokens])

    logger.debug("Truncated from %d to %d tokens", len(words), len(combined.split()))
    return combined


# === Classification prompt ===

EXTRACTION_PROMPT = """You are extracting structured deal data from a US government document about bilateral technology partnerships.

Page content:
{text}

INSTRUCTIONS:
1. Determine if this page is about a US bilateral technology/trade deal or partnership.
2. If YES, extract the framework deal info AND all individual corporate investment commitments.
3. If NO (not about a bilateral tech deal), return {{"is_tpd": false}}

Return a JSON object with this exact structure:
{{
  "is_tpd": true,
  "parent": {{
    "title": "Short deal title",
    "summary": "One clear sentence describing the deal (max 200 chars)",
    "country_code": "GBR|JPN|KOR",
    "date_signed": "YYYY-MM-DD or null",
    "signatories": ["Name 1", "Name 2"],
    "sectors": ["AI", "Nuclear Energy", ...],
    "total_value_usd": integer or null,
    "status": "ACTIVE|PENDING|COMPLETED"
  }},
  "children": [
    {{
      "title": "Short commitment title",
      "summary": "One sentence (max 150 chars)",
      "parties": ["Company A", "Company B"],
      "deal_value_usd": integer or null,
      "sector": "Aviation & Defense",
      "commitment_details": "Brief details of the commitment",
      "status": "ACTIVE|PENDING|COMPLETED"
    }}
  ]
}}

IMPORTANT:
- Extract ALL individual corporate commitments mentioned (investments, purchases, partnerships)
- Convert dollar values to integers (e.g., "$36.2 billion" -> 36200000000)
- Use country codes: GBR (UK), JPN (Japan), KOR (South Korea)
- If a detail is not mentioned, use null
- Return ONLY the JSON, no markdown or explanation"""


class Classifier:
    """Classifies raw deals into structured Deal objects using Claude API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        prefilter_enabled: bool = True,
        truncation_enabled: bool = True,
        batch_mode: bool = False,
    ) -> None:
        self.model = model
        self.prefilter_enabled = prefilter_enabled
        self.truncation_enabled = truncation_enabled
        self.batch_mode = batch_mode
        self._client = None
        self.stats = CostOptimization(
            model_used=model,
            prefilter_enabled=prefilter_enabled,
            truncation_enabled=truncation_enabled,
            batch_mode=batch_mode,
        )

    def _get_client(self):
        """Lazy-initialize Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                logger.error("anthropic package not installed. Run: pip install anthropic")
                sys.exit(1)

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                logger.error("ANTHROPIC_API_KEY not set")
                print("\n\u274c  ANTHROPIC_API_KEY not set.")
                print("   Set it: export ANTHROPIC_API_KEY='sk-ant-...'")
                print("   Add to ~/.zshrc for persistence.")
                print("   Or use --dry-run / --fetch-only to skip classification.\n")
                sys.exit(1)
            logger.info("API key present: \u2713")
            self._client = Anthropic(api_key=api_key)
        return self._client

    def classify_page(
        self,
        raw: RawDeal,
        page_text: str,
        parent_id_prefix: str,
        deal_counter: int,
    ) -> tuple[Optional[Deal], List[Deal]]:
        """Classify a single page through the full cost optimization pipeline.

        Returns (parent_deal_or_none, list_of_child_deals).
        A single API call extracts both parent and children — token efficient.
        """
        # Layer 1: Pre-filter
        if self.prefilter_enabled and not passes_prefilter(raw):
            self.stats.prefilter_skipped += 1
            return None, []

        # Layer 2: Truncation
        text = page_text
        if self.truncation_enabled:
            text = truncate_text(text)

        # Layer 4: Cache check (before API call)
        cached = get_cached_classification(CLASSIFICATION_CACHE_DIR, text)
        if cached is not None:
            self.stats.cache_hits += 1
            return self._parse_result(cached, raw, parent_id_prefix, deal_counter)

        # Layer 3: API call (model already selected)
        result = self._call_api(text)
        if result is None:
            return None, []

        # Save to Layer 4 cache
        save_cached_classification(CLASSIFICATION_CACHE_DIR, text, result)
        self.stats.new_api_calls += 1

        return self._parse_result(result, raw, parent_id_prefix, deal_counter)

    def _call_api(self, text: str) -> Optional[dict]:
        """Make the Anthropic API call. Returns parsed JSON or None."""
        client = self._get_client()
        prompt = EXTRACTION_PROMPT.format(text=text)

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            content = response.content[0].text

            # Strip markdown code fences if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON from API: %s", e)
            return None
        except Exception as e:
            logger.error("API call failed: %s", e)
            return None

    def _parse_result(
        self,
        data: dict,
        raw: RawDeal,
        parent_id_prefix: str,
        deal_counter: int,
    ) -> tuple[Optional[Deal], List[Deal]]:
        """Convert API/cached result into Deal objects."""
        if not data.get("is_tpd", False):
            return None, []

        parent_data = data.get("parent", {})
        children_data = data.get("children", [])

        # Build parent deal
        parent_deal = None
        country_code = parent_data.get("country_code", "USA")
        parent_id = f"tpd-{country_code.lower()}-{deal_counter}"

        try:
            parent_deal = Deal(
                id=parent_id,
                parent_id=None,
                source_id=raw.source_id,
                source_url=raw.source_url,
                title=parent_data.get("title", raw.title),
                summary=parent_data.get("summary", ""),
                type=DealType.TRADE,
                status=DealStatus(parent_data.get("status", "ACTIVE")),
                parties=["United States", _country_name_from_code(country_code)],
                deal_value_usd=parent_data.get("total_value_usd"),
                country=country_code,
                date=raw.raw_date or parent_data.get("date_signed", ""),
                date_signed=parent_data.get("date_signed"),
                tags=[],
                sectors=parent_data.get("sectors", []),
                signatories=parent_data.get("signatories", []),
                source_documents=[SourceDocument(
                    label=f"{raw.source_name} source",
                    url=raw.source_url,
                )],
            )
        except (ValidationError, ValueError) as e:
            logger.error("Failed to build parent deal: %s", e)

        # Build child deals
        child_deals: List[Deal] = []
        for i, child_data in enumerate(children_data):
            try:
                child_id = f"{parent_id}-{i + 1:03d}"
                child = Deal(
                    id=child_id,
                    parent_id=parent_id,
                    source_url=raw.source_url,
                    title=child_data.get("title", ""),
                    summary=child_data.get("summary", ""),
                    type=DealType.BUSINESS,
                    status=DealStatus(child_data.get("status", "ACTIVE")),
                    parties=child_data.get("parties", []),
                    deal_value_usd=child_data.get("deal_value_usd"),
                    country=country_code,
                    date=raw.raw_date or "",
                    sectors=[child_data.get("sector", "")] if child_data.get("sector") else [],
                    commitment_details=child_data.get("commitment_details"),
                )
                child_deals.append(child)
            except (ValidationError, ValueError) as e:
                logger.error("Failed to build child deal %d: %s", i, e)
                continue

        return parent_deal, child_deals

    def estimate_cost(self) -> float:
        """Rough cost estimate based on model and call count."""
        if "haiku" in self.model:
            per_call = 0.001  # ~800 input + ~500 output tokens at haiku rates
        elif "sonnet" in self.model:
            per_call = 0.005
        else:
            per_call = 0.03  # Opus
        cost = self.stats.new_api_calls * per_call
        if self.batch_mode:
            cost *= 0.5
        self.stats.estimated_cost_usd = round(cost, 4)
        return cost


def _country_name_from_code(code: str) -> str:
    """Look up full country name from ISO code."""
    for _key, info in COUNTRY_WATCHLIST.items():
        if info["code"] == code:
            return info.get("formal_name", _key)
    return code


# === Standalone test mode ===

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Classify a sample deal")
    parser.add_argument("--test-filter", action="store_true", help="Test pre-filter")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    if args.test_filter:
        samples = [
            RawDeal(title="US-Korea Technology Prosperity Deal", source_url="http://example.com", snippet="bilateral agreement on AI"),
            RawDeal(title="Weather Report for Tuesday", source_url="http://example.com", snippet="sunny skies expected"),
            RawDeal(title="Japan trade partnership in semiconductors", source_url="http://example.com", snippet="investment deal"),
        ]
        for s in samples:
            result = passes_prefilter(s)
            print(f"  {'PASS' if result else 'SKIP'}: {s.title}")
    elif args.test:
        sample_text = """
        Fact Sheet: US-Korea Technology Prosperity Deal
        President Trump and Korean leaders signed a technology prosperity deal.
        Key commitments include:
        - Korean Air: $36.2 billion purchase of 103 Boeing aircraft
        - Amazon AWS: $5 billion cloud investment through 2031
        - HD Hyundai/Cerberus: $5 billion shipbuilding investment
        Sectors: AI, 6G, biotech, defense
        """
        raw = RawDeal(
            title="US-Korea Technology Prosperity Deal",
            source_url="https://example.com/test",
            snippet=sample_text,
            raw_date="2025-10-29",
            source_name="test",
        )
        classifier = Classifier()
        parent, children = classifier.classify_page(raw, sample_text, "tpd-kor", 1)
        if parent:
            print(f"\nParent: {parent.title}")
            print(f"  Country: {parent.country}, Value: {parent.deal_value_usd}")
        for c in children:
            print(f"  Child: {c.title} — ${c.deal_value_usd}")
    else:
        parser.print_help()

"""Federal Register scraper — uses the free public JSON API.

Best data source: structured JSON, no auth, full-text search, date filtering.
API docs: https://www.federalregister.gov/developers/documentation/api/v1

Caching: Each API request URL is cached by URL hash (Layer 1).
Returns structured JSON so we skip Layer 2 (HTML extraction) —
we build RawDeal directly from the JSON fields, saving parsing work.
"""
from __future__ import annotations

import json
import logging
from typing import List
from urllib.parse import quote_plus

from pipeline.config import COUNTRY_WATCHLIST, SOURCES
from pipeline.models import RawDeal
from pipeline.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Fields we request — only what we need, reduces response size
_FIELDS = ["title", "abstract", "document_number", "publication_date", "html_url", "type"]
_FIELDS_QS = "&".join(f"fields%5B%5D={f}" for f in _FIELDS)


def _build_fr_url(base: str, term: str, per_page: int = 20) -> str:
    """Build a Federal Register API search URL.

    Uses bracket-encoded params matching the FR API's PHP-style format.
    We skip the agencies filter since it causes 400 errors with
    certain combinations — the term search alone is sufficient.
    """
    encoded_term = quote_plus(term)
    return (
        f"{base}"
        f"?conditions%5Bterm%5D={encoded_term}"
        f"&conditions%5Bpublication_date%5D%5Bgte%5D=2025-01-01"
        f"&per_page={per_page}"
        f"&page=1"
        f"&order=newest"
        f"&{_FIELDS_QS}"
    )


class FederalRegisterScraper(BaseScraper):
    """Search Federal Register for tech/trade documents related to watchlist countries."""

    @property
    def name(self) -> str:
        return "FederalRegister"

    def scrape(self) -> List[RawDeal]:
        deals: List[RawDeal] = []
        config = SOURCES["federal_register"]

        countries = COUNTRY_WATCHLIST
        if self.country_filter and self.country_filter in COUNTRY_WATCHLIST:
            countries = {self.country_filter: COUNTRY_WATCHLIST[self.country_filter]}

        for country_key, country_info in countries.items():
            country_deals = self._search_country(
                country_info["names"],
                country_info["code"],
                config,
            )
            deals.extend(country_deals)
            logger.info(
                "[%s] Found %d candidates for %s",
                self.name, len(country_deals), country_key,
            )

        return deals

    def _search_country(
        self,
        country_names: List[str],
        country_code: str,
        config: dict,
    ) -> List[RawDeal]:
        """Search FR API for documents mentioning a country + tech keywords."""
        results: List[RawDeal] = []
        primary_name = country_names[0]
        per_page = config.get("per_page", 20)

        # Focused search terms — fewer queries = less API load + more cache reuse
        search_terms = [
            f"{primary_name} technology trade",
            f"{primary_name} technology prosperity deal",
            f"{primary_name} bilateral technology agreement",
        ]

        seen_doc_numbers: set = set()

        for term in search_terms:
            url = _build_fr_url(config["search_endpoint"], term, per_page)

            page_content = self.fetch_page(url)
            if page_content is None:
                continue

            try:
                data = json.loads(page_content)
            except (json.JSONDecodeError, ValueError) as e:
                logger.error("[%s] Invalid JSON from API: %s", self.name, e)
                continue

            docs = data.get("results", [])
            total = data.get("count", 0)
            logger.info(
                "[%s] Search '%s': %d results (showing %d)",
                self.name, term, total, len(docs),
            )

            for doc in docs:
                doc_number = doc.get("document_number", "")
                if doc_number in seen_doc_numbers:
                    continue
                seen_doc_numbers.add(doc_number)

                title = doc.get("title", "")
                abstract = doc.get("abstract", "") or ""
                html_url = doc.get("html_url", "")
                pub_date = doc.get("publication_date", "")

                results.append(RawDeal(
                    title=title,
                    source_url=html_url,
                    source_id=f"FR-{doc_number}",
                    snippet=abstract[:1000],  # Cap snippet to save tokens later
                    raw_date=pub_date,
                    source_name="federal_register",
                ))

        return results

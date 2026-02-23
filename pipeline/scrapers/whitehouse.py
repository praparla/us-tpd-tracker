"""White House scraper — paginates fact-sheets and articles listing pages.

Strategy (optimized for caching):
  1. Fetch listing pages (cached Layer 1) — just titles + links
  2. Filter titles by country watchlist + keywords (zero-cost string match)
  3. Only fetch full pages for matches (cached Layer 1)
  4. Extract clean text from matches (cached Layer 2)

This means we never fetch pages that don't match our watchlist,
and matched pages are only fetched/parsed once across all runs.
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

from pipeline.config import SOURCES
from pipeline.models import RawDeal
from pipeline.scrapers.base import BaseScraper, title_matches_watchlist

logger = logging.getLogger(__name__)


class WhiteHouseScraper(BaseScraper):
    """Scrape whitehouse.gov fact sheets and articles for TPD-related content."""

    @property
    def name(self) -> str:
        return "WhiteHouse"

    def scrape(self) -> List[RawDeal]:
        deals: List[RawDeal] = []
        config = SOURCES["whitehouse"]
        max_pages = config.get("max_pages", 10)

        # Scrape both fact sheets and articles listing pages
        for section_key in ["fact_sheets", "articles"]:
            url_template = config.get(section_key)
            if not url_template:
                continue

            section_deals = self._scrape_listing(
                url_template, max_pages, section_key,
            )
            deals.extend(section_deals)

        return deals

    def _scrape_listing(
        self,
        url_template: str,
        max_pages: int,
        section: str,
    ) -> List[RawDeal]:
        """Paginate through a listing page and find matching articles."""
        results: List[RawDeal] = []
        seen_urls: set = set()

        for page_num in range(1, max_pages + 1):
            url = url_template.format(page=page_num)
            html = self.fetch_page(url)
            if html is None:
                logger.info(
                    "[%s] No more pages at %s page %d",
                    self.name, section, page_num,
                )
                break

            # Parse listing to get article titles + links
            candidates = self._parse_listing_page(html)
            if not candidates:
                logger.info(
                    "[%s] No candidates found on %s page %d, stopping",
                    self.name, section, page_num,
                )
                break

            matched = 0
            for title, link in candidates:
                if link in seen_urls:
                    continue
                seen_urls.add(link)

                # Cheap title-based filter — no network, no AI
                if not title_matches_watchlist(title, self.country_filter):
                    continue

                matched += 1
                # Fetch + extract text for matching pages (cached Layers 1+2)
                text = self.fetch_and_extract(link)
                snippet = text[:1000] if text else ""

                # Try to extract date from URL pattern like /2025/09/
                raw_date = self._extract_date_from_url(link)

                results.append(RawDeal(
                    title=title,
                    source_url=link,
                    source_id="",
                    snippet=snippet,
                    raw_date=raw_date,
                    source_name="whitehouse",
                ))

            logger.info(
                "[%s] %s page %d: %d candidates, %d matched watchlist",
                self.name, section, page_num, len(candidates), matched,
            )

        return results

    def _parse_listing_page(self, html: str) -> List[Tuple[str, str]]:
        """Extract (title, url) pairs from a WH listing page."""
        soup = BeautifulSoup(html, "lxml")
        results: List[Tuple[str, str]] = []

        # WH listing pages use various patterns — try common ones
        # Look for article links in the main content area
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title = a_tag.get_text(strip=True)

            # Skip empty titles, navigation links, very short text
            if not title or len(title) < 10:
                continue

            # Only follow links to WH articles/fact-sheets/presidential-actions
            if not any(
                segment in href
                for segment in ["/articles/", "/fact-sheets/", "/presidential-actions/"]
            ):
                continue

            # Normalize URL
            if href.startswith("/"):
                href = "https://www.whitehouse.gov" + href

            results.append((title, href))

        return results

    def _extract_date_from_url(self, url: str) -> str:
        """Try to extract YYYY-MM-DD from URL like /2025/09/some-article/."""
        match = re.search(r"/(\d{4})/(\d{2})/", url)
        if match:
            return f"{match.group(1)}-{match.group(2)}-01"
        return ""

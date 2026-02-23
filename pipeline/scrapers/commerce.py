"""Commerce.gov scraper — paginates fact-sheets and press-releases listing pages.

Same caching strategy as whitehouse.py:
  1. Listing pages cached (Layer 1)
  2. Title-based filtering (zero cost)
  3. Full pages fetched only for matches (Layer 1)
  4. Text extraction cached (Layer 2)
"""
from __future__ import annotations

import logging
import re
from typing import List, Tuple

from bs4 import BeautifulSoup

from pipeline.config import SOURCES
from pipeline.models import RawDeal
from pipeline.scrapers.base import BaseScraper, title_matches_watchlist

logger = logging.getLogger(__name__)


class CommerceScraper(BaseScraper):
    """Scrape commerce.gov fact sheets and press releases for TPD content."""

    @property
    def name(self) -> str:
        return "Commerce"

    def scrape(self) -> List[RawDeal]:
        deals: List[RawDeal] = []
        config = SOURCES["commerce"]
        max_pages = config.get("max_pages", 5)

        for section_key in ["fact_sheets", "press_releases"]:
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
        """Paginate through commerce.gov listing and find matching articles."""
        results: List[RawDeal] = []
        seen_urls: set = set()

        for page_num in range(0, max_pages):  # commerce.gov uses 0-indexed pages
            url = url_template.format(page=page_num)
            html = self.fetch_page(url)
            if html is None:
                break

            candidates = self._parse_listing_page(html)
            if not candidates:
                logger.info(
                    "[%s] No candidates on %s page %d, stopping",
                    self.name, section, page_num,
                )
                break

            matched = 0
            for title, link in candidates:
                if link in seen_urls:
                    continue
                seen_urls.add(link)

                if not title_matches_watchlist(title, self.country_filter):
                    continue

                matched += 1
                text = self.fetch_and_extract(link)
                snippet = text[:1000] if text else ""
                raw_date = self._extract_date_from_url(link)

                results.append(RawDeal(
                    title=title,
                    source_url=link,
                    source_id="",
                    snippet=snippet,
                    raw_date=raw_date,
                    source_name="commerce",
                ))

            logger.info(
                "[%s] %s page %d: %d candidates, %d matched",
                self.name, section, page_num, len(candidates), matched,
            )

        return results

    def _parse_listing_page(self, html: str) -> List[Tuple[str, str]]:
        """Extract (title, url) pairs from a Commerce.gov listing page."""
        soup = BeautifulSoup(html, "lxml")
        results: List[Tuple[str, str]] = []

        # Commerce.gov news listings typically use article/teaser patterns
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title = a_tag.get_text(strip=True)

            if not title or len(title) < 10:
                continue

            # Only follow links to commerce.gov news content
            if not any(
                segment in href
                for segment in ["/news/", "/fact-sheets/", "/press-releases/"]
            ):
                continue

            if href.startswith("/"):
                href = "https://www.commerce.gov" + href

            results.append((title, href))

        return results

    def _extract_date_from_url(self, url: str) -> str:
        """Try to extract date from URL like /2026/02/fact-sheet-..."""
        match = re.search(r"/(\d{4})/(\d{2})/", url)
        if match:
            return f"{match.group(1)}-{match.group(2)}-01"
        return ""

"""USTR.gov scraper — scrapes fact sheets and press releases listing pages.

Same caching strategy as other HTML scrapers:
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


class USTRScraper(BaseScraper):
    """Scrape USTR.gov fact sheets and press releases for trade deal content."""

    @property
    def name(self) -> str:
        return "USTR"

    def scrape(self) -> List[RawDeal]:
        deals: List[RawDeal] = []
        config = SOURCES["ustr"]
        max_pages = config.get("max_pages", 5)

        for section_key in ["fact_sheets", "press_releases"]:
            base_url = config.get(section_key)
            if not base_url:
                continue

            section_deals = self._scrape_listing(
                base_url, max_pages, section_key,
            )
            deals.extend(section_deals)

        return deals

    def _scrape_listing(
        self,
        base_url: str,
        max_pages: int,
        section: str,
    ) -> List[RawDeal]:
        """Fetch USTR listing pages and find matching articles."""
        results: List[RawDeal] = []
        seen_urls: set = set()

        # USTR uses ?page=N for pagination
        for page_num in range(0, max_pages):
            if page_num == 0:
                url = base_url
            else:
                url = f"{base_url}?page={page_num}"

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
                    source_name="ustr",
                ))

            logger.info(
                "[%s] %s page %d: %d candidates, %d matched",
                self.name, section, page_num, len(candidates), matched,
            )

        return results

    def _parse_listing_page(self, html: str) -> List[Tuple[str, str]]:
        """Extract (title, url) pairs from a USTR listing page."""
        soup = BeautifulSoup(html, "lxml")
        results: List[Tuple[str, str]] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title = a_tag.get_text(strip=True)

            if not title or len(title) < 10:
                continue

            # Follow links to USTR content pages
            if not any(
                segment in href
                for segment in [
                    "/fact-sheets/", "/press-releases/", "/trade-agreements/",
                    "/about-us/policy-offices/",
                ]
            ):
                continue

            if href.startswith("/"):
                href = "https://ustr.gov" + href

            results.append((title, href))

        return results

    def _extract_date_from_url(self, url: str) -> str:
        """Try to extract date from USTR URL patterns."""
        match = re.search(r"/(\d{4})/(\w+)/", url)
        if match:
            year = match.group(1)
            month_str = match.group(2)
            # USTR sometimes uses month names like "may", "october"
            month_map = {
                "january": "01", "february": "02", "march": "03", "april": "04",
                "may": "05", "june": "06", "july": "07", "august": "08",
                "september": "09", "october": "10", "november": "11", "december": "12",
            }
            month = month_map.get(month_str.lower(), month_str.zfill(2))
            if len(month) == 2 and month.isdigit():
                return f"{year}-{month}-01"
        return ""

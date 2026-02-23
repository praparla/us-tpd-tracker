"""Base scraper with caching, rate limiting, and retry logic.

Caching strategy (optimized for minimal compute/tokens):
  Layer 1: Raw HTML page cache (pipeline/.cache/pages/) — keyed by URL hash.
           Re-runs never re-download. Survives across sessions.
  Layer 2: Extracted text cache (pipeline/.cache/extracted/) — keyed by URL hash.
           Parsed clean text stored separately so we never re-parse HTML.
  Layer 3: Classification cache in classifier.py — keyed by content hash.

This means a full re-run with warm caches does ZERO network requests,
ZERO HTML parsing, and ZERO API calls.
"""
from __future__ import annotations

import abc
import logging
import re
import time
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from pipeline.cache import get_cached_page, save_cached_page
from pipeline.config import (
    BACKOFF_START_SECONDS,
    CACHE_DIR,
    COUNTRY_WATCHLIST,
    DEAL_KEYWORDS,
    MAX_RETRIES,
    PAGE_CACHE_DIR,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    TECH_KEYWORDS,
    USER_AGENT,
)
from pipeline.models import RawDeal

logger = logging.getLogger(__name__)

# Layer 2: extracted text cache dir
EXTRACTED_CACHE_DIR = CACHE_DIR / "extracted"


def _get_extracted_text(url: str) -> Optional[str]:
    """Retrieve cached extracted text for a URL."""
    from pipeline.cache import url_hash
    cache_file = EXTRACTED_CACHE_DIR / f"{url_hash(url)}.txt"
    if cache_file.exists():
        logger.debug("Cache HIT (extracted): %s", url)
        return cache_file.read_text(encoding="utf-8")
    return None


def _save_extracted_text(url: str, text: str) -> None:
    """Save extracted text to cache."""
    from pipeline.cache import url_hash
    EXTRACTED_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = EXTRACTED_CACHE_DIR / f"{url_hash(url)}.txt"
    cache_file.write_text(text, encoding="utf-8")
    logger.debug("Cached extracted text: %s -> %s", url, cache_file.name)


def extract_text_from_html(html: str) -> str:
    """Extract clean article text from HTML, stripping nav/scripts/footers.

    This is cached (Layer 2) so we only parse each page once.
    The output is what gets sent to the AI classifier — keeping it
    clean and minimal saves tokens.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove non-content elements
    for tag in soup.find_all(["script", "style", "nav", "header", "footer",
                              "aside", "iframe", "noscript", "form"]):
        tag.decompose()

    # Try to find the main content area
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_=re.compile(r"content|entry|post|article", re.I))
        or soup.find("div", id=re.compile(r"content|entry|post|article", re.I))
        or soup.body
    )
    if main is None:
        main = soup

    # Get text, collapse whitespace
    text = main.get_text(separator="\n", strip=True)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def title_matches_watchlist(title: str, country_filter: Optional[str] = None) -> bool:
    """Check if a page title matches country watchlist + tech/deal keywords.

    This is the cheapest possible filter — pure string matching,
    no AI, no network. Runs on listing page titles to decide which
    pages are worth fetching.
    """
    title_lower = title.lower()

    # Check country match
    countries_to_check = COUNTRY_WATCHLIST
    if country_filter and country_filter in COUNTRY_WATCHLIST:
        countries_to_check = {country_filter: COUNTRY_WATCHLIST[country_filter]}

    country_match = False
    for _key, info in countries_to_check.items():
        for name in info["names"]:
            if name.lower() in title_lower:
                country_match = True
                break
        if country_match:
            break

    if not country_match:
        return False

    # Check tech OR deal keyword match
    all_keywords = TECH_KEYWORDS + DEAL_KEYWORDS
    for kw in all_keywords:
        if kw.lower() in title_lower:
            return True

    return False


class BaseScraper(abc.ABC):
    """Abstract base for all scrapers.

    Subclasses implement discover() to find candidate URLs from listing pages,
    and scrape() to return RawDeal objects.
    """

    def __init__(self, country_filter: Optional[str] = None) -> None:
        self._client: Optional[httpx.Client] = None
        self._last_request_time: dict[str, float] = {}
        self.country_filter = country_filter

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT_SECONDS,
                follow_redirects=True,
            )
        return self._client

    def _rate_limit(self, host: str) -> None:
        """Enforce minimum delay between requests to the same host."""
        last = self._last_request_time.get(host, 0)
        elapsed = time.time() - last
        if elapsed < REQUEST_DELAY_SECONDS:
            sleep_time = REQUEST_DELAY_SECONDS - elapsed
            logger.debug("Rate limiting: sleeping %.1fs for %s", sleep_time, host)
            time.sleep(sleep_time)
        self._last_request_time[host] = time.time()

    def fetch_page(
        self,
        url: str,
        method: str = "GET",
        json_body: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> Optional[str]:
        """Fetch a URL with Layer 1 caching, rate limiting, and retry.

        For POST requests with json_body, the cache key includes the body hash
        to distinguish different searches to the same endpoint.
        """
        # Build cache key (include body for POST requests)
        cache_key = url
        if json_body:
            import json
            cache_key = url + "|" + json.dumps(json_body, sort_keys=True)
        if params:
            import json
            cache_key = url + "?" + json.dumps(params, sort_keys=True)

        # Layer 1: check page cache
        cached = get_cached_page(PAGE_CACHE_DIR, cache_key)
        if cached is not None:
            return cached

        host = urlparse(url).hostname or url
        client = self._get_client()

        for attempt in range(MAX_RETRIES):
            self._rate_limit(host)
            try:
                if method == "POST" and json_body:
                    response = client.post(url, json=json_body)
                else:
                    response = client.get(url, params=params)

                logger.info("[%s] %s %s -> %d", self.name, method, url, response.status_code)

                if response.status_code == 429:
                    wait = BACKOFF_START_SECONDS * (2 ** attempt)
                    logger.warning("429 rate limited. Backing off %ds", wait)
                    time.sleep(wait)
                    continue

                if response.status_code == 404:
                    logger.warning("[%s] 404 Not Found: %s", self.name, url)
                    return None

                # Don't retry client errors (4xx) — they won't change
                if 400 <= response.status_code < 500:
                    logger.warning(
                        "[%s] Client error %d for %s",
                        self.name, response.status_code, url,
                    )
                    return None

                response.raise_for_status()
                content = response.text

                # Save to Layer 1 cache
                save_cached_page(PAGE_CACHE_DIR, cache_key, content)
                return content

            except httpx.HTTPError as e:
                logger.error(
                    "[%s] Request failed (attempt %d/%d): %s",
                    self.name, attempt + 1, MAX_RETRIES, e,
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_START_SECONDS * (2 ** attempt))

        return None

    def fetch_and_extract(self, url: str) -> Optional[str]:
        """Fetch a page and extract clean text, with Layer 2 caching.

        This is the method scrapers should call when they want article text.
        Returns clean text ready for AI classification.
        """
        # Layer 2: check extracted text cache first
        cached_text = _get_extracted_text(url)
        if cached_text is not None:
            return cached_text

        # Layer 1: fetch raw HTML (cached)
        html = self.fetch_page(url)
        if html is None:
            return None

        # Parse and cache extracted text (Layer 2)
        text = extract_text_from_html(html)
        _save_extracted_text(url, text)
        return text

    @abc.abstractmethod
    def scrape(self) -> List[RawDeal]:
        """Return raw deal candidates. Subclasses implement this."""
        ...

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

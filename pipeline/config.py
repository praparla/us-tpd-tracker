"""All constants and toggles for the US Tech Prosperity Deal Tracker pipeline."""
from __future__ import annotations

from pathlib import Path

# === Versioning ===
SCRAPER_VERSION = "1.0.0"

# === MVP Cap ===
MAX_DEALS_TO_PROCESS = 50  # TODO: Remove cap for production

# === Paths ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
PAGE_CACHE_DIR = CACHE_DIR / "pages"
CLASSIFICATION_CACHE_DIR = CACHE_DIR / "classifications"

# === Network ===
USER_AGENT = "us-tpd-tracker/1.0 (github.com/praparla/us-tpd-tracker)"
REQUEST_DELAY_SECONDS = 1.5
BACKOFF_START_SECONDS = 10
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30

# === Country Watchlist ===
# Adding a new country = one entry here. All scrapers pick it up automatically.
COUNTRY_WATCHLIST: dict[str, dict] = {
    "UK": {
        "names": [
            "United Kingdom", "UK", "U.K.",
            "Britain", "British", "Great Britain",
            "England",  # colloquial — some articles use it loosely
        ],
        "code": "GBR",
        "formal_name": "United Kingdom of Great Britain and Northern Ireland",
    },
    "Japan": {
        "names": [
            "Japan", "Japanese",
            "JPN",  # ISO code sometimes appears in titles
        ],
        "code": "JPN",
        "formal_name": "Japan",
    },
    "South Korea": {
        "names": [
            "South Korea", "Korea", "Korean",
            "Republic of Korea", "ROK", "R.O.K.",
            "S. Korea",
        ],
        "code": "KOR",
        "formal_name": "Republic of Korea",
    },
}

# === Search Keywords ===
TECH_KEYWORDS = [
    "technology", "AI", "artificial intelligence", "semiconductor", "quantum",
    "6G", "biotech", "biotechnology", "nuclear", "fusion", "cyber", "digital",
    "chip", "data center", "cloud", "software", "manufacturing", "computing",
    "telecom", "telecommunications", "robotics", "space",
]

DEAL_KEYWORDS = [
    "prosperity", "trade deal", "partnership", "agreement", "investment",
    "bilateral", "memorandum", "MOU", "commitment", "contract", "deal",
    "cooperation", "framework", "pact", "accord",
]

# === Data Sources ===
SOURCES: dict[str, dict] = {
    "federal_register": {
        "api_base": "https://www.federalregister.gov/api/v1",
        "search_endpoint": "https://www.federalregister.gov/api/v1/documents.json",
        "agencies": [
            "commerce-department",
            "state-department",
            "international-trade-administration",
            "office-of-the-united-states-trade-representative",
        ],
        "per_page": 50,
    },
    "whitehouse": {
        "fact_sheets": "https://www.whitehouse.gov/fact-sheets/page/{page}/",
        "articles": "https://www.whitehouse.gov/articles/page/{page}/",
        "max_pages": 25,  # TPDs from late 2025 are deep in pagination
    },
    "commerce": {
        "fact_sheets": "https://www.commerce.gov/news/fact-sheets?page={page}",
        "press_releases": "https://www.commerce.gov/news/press-releases?page={page}",
        "max_pages": 5,
    },
    "ustr": {
        "fact_sheets": "https://ustr.gov/about-us/policy-offices/press-office/fact-sheets",
        "press_releases": "https://ustr.gov/about-us/policy-offices/press-office/press-releases",
        "max_pages": 5,
    },
}

# === AI Classification ===
DEFAULT_MODEL = "claude-3-5-haiku-20241022"
PREMIUM_MODEL = "claude-opus-4-5-20250220"
MAX_INPUT_TOKENS = 800

PREFILTER_KEYWORDS = TECH_KEYWORDS + DEAL_KEYWORDS

# === Cost Optimization Defaults ===
PREFILTER_ENABLED = True
TRUNCATION_ENABLED = True
BATCH_MODE = False

"""URL validation tests for deal data files.

Ensures all URLs in deals.json and deals.sample.json are well-formed
and point to known government sources.
Run with: PYTHONPATH=. python3 -m pytest tests/test_urls.py -v
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest


# ── Fixtures ────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

ALLOWED_DOMAINS = {
    "www.whitehouse.gov",
    "whitehouse.gov",
    "www.commerce.gov",
    "commerce.gov",
    "ustr.gov",
    "www.ustr.gov",
    "www.federalregister.gov",
    "federalregister.gov",
}


@pytest.fixture
def deals_data() -> dict:
    return json.loads((DATA_DIR / "deals.json").read_text())


@pytest.fixture
def sample_data() -> dict:
    return json.loads((DATA_DIR / "deals.sample.json").read_text())


def _collect_all_urls(data: dict) -> list[tuple[str, str]]:
    """Collect all URLs from a deals data file, with their deal ID for context."""
    urls = []
    for deal in data["items"]:
        deal_id = deal["id"]
        if deal.get("source_url"):
            urls.append((deal_id, deal["source_url"]))
        for doc in deal.get("source_documents", []):
            if doc.get("url"):
                urls.append((f"{deal_id}/source_doc:{doc['label']}", doc["url"]))
    return urls


# ── URL format tests ───────────────────────────────────────────────

class TestUrlFormat:
    """Check that all URLs are well-formed."""

    def test_all_source_urls_are_https(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            url = deal["source_url"]
            assert url.startswith("https://"), (
                f"Deal {deal['id']} source_url not HTTPS: {url}"
            )

    def test_all_source_document_urls_are_https(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            for doc in deal.get("source_documents", []):
                url = doc["url"]
                assert url.startswith("https://"), (
                    f"Deal {deal['id']} source_doc '{doc['label']}' not HTTPS: {url}"
                )

    def test_no_trailing_spaces_in_urls(self, deals_data: dict) -> None:
        for deal_id, url in _collect_all_urls(deals_data):
            assert url == url.strip(), f"{deal_id} has URL with whitespace: '{url}'"

    def test_urls_are_parseable(self, deals_data: dict) -> None:
        for deal_id, url in _collect_all_urls(deals_data):
            parsed = urlparse(url)
            assert parsed.scheme in ("http", "https"), f"{deal_id}: bad scheme in {url}"
            assert parsed.netloc, f"{deal_id}: missing netloc in {url}"


class TestUrlDomains:
    """Check that URLs point to known government domains."""

    def test_source_urls_are_government_domains(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            domain = urlparse(deal["source_url"]).netloc
            assert domain in ALLOWED_DOMAINS, (
                f"Deal {deal['id']} source_url has unexpected domain: {domain}"
            )

    def test_source_document_urls_are_government_domains(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            for doc in deal.get("source_documents", []):
                domain = urlparse(doc["url"]).netloc
                assert domain in ALLOWED_DOMAINS, (
                    f"Deal {deal['id']} source_doc '{doc['label']}' "
                    f"has unexpected domain: {domain}"
                )


class TestUrlConsistency:
    """Check URL consistency within and across data files."""

    def test_child_deals_use_parent_urls(self, deals_data: dict) -> None:
        """Child deals should reference URLs that appear in parent source_documents."""
        parent_urls: dict[str, set[str]] = {}
        for deal in deals_data["items"]:
            if deal.get("parent_id") is None:
                urls = {deal["source_url"]}
                for doc in deal.get("source_documents", []):
                    urls.add(doc["url"])
                parent_urls[deal["id"]] = urls

        for deal in deals_data["items"]:
            pid = deal.get("parent_id")
            if pid and pid in parent_urls:
                assert deal["source_url"] in parent_urls[pid], (
                    f"Child {deal['id']} source_url {deal['source_url']} "
                    f"not in parent {pid} URLs"
                )

    def test_no_duplicate_urls_in_source_documents(self, deals_data: dict) -> None:
        for deal in deals_data["items"]:
            urls = [doc["url"] for doc in deal.get("source_documents", [])]
            assert len(urls) == len(set(urls)), (
                f"Deal {deal['id']} has duplicate source_document URLs"
            )


class TestSampleUrlFormat:
    """Check URLs in sample data too."""

    def test_sample_source_urls_are_https(self, sample_data: dict) -> None:
        for deal in sample_data["items"]:
            url = deal["source_url"]
            assert url.startswith("https://"), (
                f"Sample deal {deal['id']} source_url not HTTPS: {url}"
            )

    def test_sample_source_urls_are_government_domains(self, sample_data: dict) -> None:
        for deal in sample_data["items"]:
            domain = urlparse(deal["source_url"]).netloc
            assert domain in ALLOWED_DOMAINS, (
                f"Sample deal {deal['id']} has unexpected domain: {domain}"
            )

    def test_sample_source_document_urls_valid(self, sample_data: dict) -> None:
        for deal in sample_data["items"]:
            for doc in deal.get("source_documents", []):
                url = doc["url"]
                assert url.startswith("https://"), (
                    f"Sample {deal['id']} doc '{doc['label']}' not HTTPS: {url}"
                )
                domain = urlparse(url).netloc
                assert domain in ALLOWED_DOMAINS, (
                    f"Sample {deal['id']} doc '{doc['label']}' bad domain: {domain}"
                )


class TestSampleErrorUrls:
    """Validate URLs in the errors array."""

    def test_error_urls_are_urls(self, sample_data: dict) -> None:
        for err in sample_data["meta"].get("errors", []):
            source = err.get("source", "")
            if source:
                assert source.startswith("http"), (
                    f"Error source doesn't look like a URL: {source}"
                )

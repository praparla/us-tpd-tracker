"""Unit tests for the cache module.

Tests url_hash, content_hash, page cache, classification cache, and cache clearing.
Run with: PYTHONPATH=. python3 -m pytest tests/test_cache.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.cache import (
    clear_cache,
    content_hash,
    get_cached_classification,
    get_cached_page,
    save_cached_classification,
    save_cached_page,
    url_hash,
)


class TestUrlHash:
    """Test URL hashing for cache keys."""

    def test_deterministic(self) -> None:
        assert url_hash("https://example.com") == url_hash("https://example.com")

    def test_different_urls_different_hashes(self) -> None:
        assert url_hash("https://a.com") != url_hash("https://b.com")

    def test_returns_hex_string(self) -> None:
        h = url_hash("https://example.com")
        assert isinstance(h, str)
        assert len(h) == 16
        int(h, 16)  # should not raise

    def test_empty_string(self) -> None:
        h = url_hash("")
        assert isinstance(h, str)
        assert len(h) == 16


class TestContentHash:
    """Test content hashing for classification cache keys."""

    def test_deterministic(self) -> None:
        assert content_hash("hello world") == content_hash("hello world")

    def test_different_content_different_hashes(self) -> None:
        assert content_hash("content A") != content_hash("content B")

    def test_returns_hex_string(self) -> None:
        h = content_hash("some text")
        assert isinstance(h, str)
        assert len(h) == 16
        int(h, 16)

    def test_sensitive_to_whitespace(self) -> None:
        assert content_hash("hello") != content_hash("hello ")


class TestPageCache:
    """Test page cache read/write."""

    def test_miss_returns_none(self, tmp_path: Path) -> None:
        assert get_cached_page(tmp_path, "https://nonexistent.com") is None

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        url = "https://example.com/page"
        content = "<html><body>test</body></html>"
        save_cached_page(tmp_path, url, content)
        assert get_cached_page(tmp_path, url) == content

    def test_different_urls_separate_files(self, tmp_path: Path) -> None:
        save_cached_page(tmp_path, "https://a.com", "content A")
        save_cached_page(tmp_path, "https://b.com", "content B")
        assert get_cached_page(tmp_path, "https://a.com") == "content A"
        assert get_cached_page(tmp_path, "https://b.com") == "content B"

    def test_creates_directory(self, tmp_path: Path) -> None:
        cache_dir = tmp_path / "subdir" / "cache"
        save_cached_page(cache_dir, "https://example.com", "content")
        assert cache_dir.exists()

    def test_overwrites_existing(self, tmp_path: Path) -> None:
        url = "https://example.com"
        save_cached_page(tmp_path, url, "old")
        save_cached_page(tmp_path, url, "new")
        assert get_cached_page(tmp_path, url) == "new"


class TestClassificationCache:
    """Test classification result cache read/write."""

    def test_miss_returns_none(self, tmp_path: Path) -> None:
        assert get_cached_classification(tmp_path, "some text") is None

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        text = "Japan technology prosperity deal"
        result = {"is_tpd": True, "parent": {"title": "Test"}}
        save_cached_classification(tmp_path, text, result)
        cached = get_cached_classification(tmp_path, text)
        assert cached == result

    def test_json_roundtrip(self, tmp_path: Path) -> None:
        text = "test content"
        result = {
            "is_tpd": True,
            "parent": {"title": "Deal", "value": 1000000000},
            "children": [{"title": "Child", "value": None}],
        }
        save_cached_classification(tmp_path, text, result)
        cached = get_cached_classification(tmp_path, text)
        assert cached["parent"]["value"] == 1000000000
        assert cached["children"][0]["value"] is None


class TestClearCache:
    """Test cache clearing."""

    def test_clear_empty_dir(self, tmp_path: Path) -> None:
        assert clear_cache(tmp_path) == 0

    def test_clear_nonexistent_dir(self, tmp_path: Path) -> None:
        assert clear_cache(tmp_path / "nonexistent") == 0

    def test_clears_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.html").write_text("a")
        (tmp_path / "b.json").write_text("b")
        assert clear_cache(tmp_path) == 2
        assert list(tmp_path.glob("*")) == []

    def test_preserves_subdirectories(self, tmp_path: Path) -> None:
        (tmp_path / "file.txt").write_text("x")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("y")
        cleared = clear_cache(tmp_path)
        assert cleared == 1  # only top-level file
        assert subdir.exists()

"""Disk cache helpers for the pipeline.

Caches fetched pages by URL hash and classification results by content hash.
All cache files are stored under pipeline/.cache/ (gitignored).
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def content_hash(content: str) -> str:
    """Hash content for cache key (classification results)."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def url_hash(url: str) -> str:
    """Hash URL for cache key (fetched pages)."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def get_cached_page(cache_dir: Path, url: str) -> Optional[str]:
    """Retrieve a cached page by URL. Returns None on cache miss."""
    cache_file = cache_dir / f"{url_hash(url)}.html"
    if cache_file.exists():
        logger.debug("Cache HIT (page): %s", url)
        return cache_file.read_text(encoding="utf-8")
    logger.debug("Cache MISS (page): %s", url)
    return None


def save_cached_page(cache_dir: Path, url: str, content: str) -> Path:
    """Save a fetched page to disk cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{url_hash(url)}.html"
    cache_file.write_text(content, encoding="utf-8")
    logger.info("Cached page: %s -> %s", url, cache_file.name)
    return cache_file


def get_cached_classification(cache_dir: Path, raw_text: str) -> Optional[dict]:
    """Retrieve a cached classification result by content hash."""
    cache_file = cache_dir / f"{content_hash(raw_text)}.json"
    if cache_file.exists():
        logger.debug("Cache HIT (classification): %s", cache_file.name)
        return json.loads(cache_file.read_text(encoding="utf-8"))
    logger.debug("Cache MISS (classification): %s", cache_file.name)
    return None


def save_cached_classification(cache_dir: Path, raw_text: str, result: dict) -> Path:
    """Save a classification result to disk cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{content_hash(raw_text)}.json"
    cache_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logger.info("Cached classification: %s", cache_file.name)
    return cache_file


def clear_cache(cache_dir: Path) -> int:
    """Delete all cached files in a directory. Returns count of files deleted."""
    count = 0
    if cache_dir.exists():
        for f in cache_dir.glob("*"):
            if f.is_file():
                f.unlink()
                count += 1
    logger.info("Cleared %d cached files from %s", count, cache_dir)
    return count

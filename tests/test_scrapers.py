"""Unit tests for scraper base module.

Tests HTML text extraction and title matching (no network calls).
Run with: PYTHONPATH=. python3 -m pytest tests/test_scrapers.py -v
"""
from __future__ import annotations

import pytest

from pipeline.scrapers.base import extract_text_from_html, title_matches_watchlist


# ── HTML text extraction ───────────────────────────────────────────

class TestExtractTextFromHtml:
    """Test the HTML → clean text extraction."""

    def test_basic_html(self) -> None:
        html = "<html><body><p>Hello world</p></body></html>"
        text = extract_text_from_html(html)
        assert "Hello world" in text

    def test_strips_scripts(self) -> None:
        html = """
        <html><body>
        <script>alert('xss')</script>
        <p>Real content</p>
        </body></html>
        """
        text = extract_text_from_html(html)
        assert "alert" not in text
        assert "Real content" in text

    def test_strips_nav_and_footer(self) -> None:
        html = """
        <html><body>
        <nav><a href="/">Home</a></nav>
        <article><p>Article content</p></article>
        <footer>Copyright 2025</footer>
        </body></html>
        """
        text = extract_text_from_html(html)
        assert "Article content" in text
        # Nav/footer content should be removed
        assert "Copyright 2025" not in text

    def test_prefers_article_tag(self) -> None:
        html = """
        <html><body>
        <div>Sidebar stuff</div>
        <article><h1>Main Article</h1><p>Content here</p></article>
        </body></html>
        """
        text = extract_text_from_html(html)
        assert "Main Article" in text

    def test_collapses_blank_lines(self) -> None:
        html = "<html><body><p>A</p><br><br><br><br><p>B</p></body></html>"
        text = extract_text_from_html(html)
        # Should not have 4+ blank lines
        assert "\n\n\n\n" not in text

    def test_empty_html(self) -> None:
        text = extract_text_from_html("")
        assert text == ""

    def test_strips_style_tags(self) -> None:
        html = "<html><head><style>body{color:red}</style></head><body><p>Content</p></body></html>"
        text = extract_text_from_html(html)
        assert "color:red" not in text
        assert "Content" in text


# ── Title matching (extended tests beyond test_data_validation.py) ─

class TestTitleMatchesWatchlist:
    """Extended title matching tests."""

    def test_prosperity_always_matches(self) -> None:
        assert title_matches_watchlist("Technology Prosperity Deal Announced")

    def test_country_plus_tech_keyword(self) -> None:
        assert title_matches_watchlist("Japan AI framework agreement")
        assert title_matches_watchlist("UK quantum computing partnership")
        assert title_matches_watchlist("South Korea semiconductor investment")

    def test_country_plus_deal_keyword(self) -> None:
        assert title_matches_watchlist("Japan bilateral trade agreement")
        assert title_matches_watchlist("Korea MOU on technology cooperation")

    def test_rejects_country_alone(self) -> None:
        """Country name without a tech/deal keyword should not match."""
        assert not title_matches_watchlist("Japan weather forecast")
        assert not title_matches_watchlist("UK sports results")

    def test_rejects_keyword_alone(self) -> None:
        """Tech/deal keyword without country should not match (unless 'prosperity')."""
        assert not title_matches_watchlist("New AI regulation in Europe")
        assert not title_matches_watchlist("Semiconductor shortage continues")

    def test_case_insensitive(self) -> None:
        assert title_matches_watchlist("JAPAN TECHNOLOGY DEAL")
        assert title_matches_watchlist("united kingdom ai partnership")

    def test_country_filter_restricts(self) -> None:
        assert title_matches_watchlist("Japan technology deal", country_filter="Japan")
        assert not title_matches_watchlist("Japan technology deal", country_filter="UK")

    def test_country_filter_unknown_checks_all(self) -> None:
        """Unknown country filter falls through to checking all countries."""
        # "France" is not a watchlist key, so all countries are checked
        assert title_matches_watchlist("Japan technology deal", country_filter="France")

    def test_korean_variant_names(self) -> None:
        assert title_matches_watchlist("ROK bilateral technology deal")
        assert title_matches_watchlist("Republic of Korea semiconductor agreement")
        assert title_matches_watchlist("Korean Air investment deal")

    def test_uk_variant_names(self) -> None:
        assert title_matches_watchlist("Britain technology partnership deal")
        assert title_matches_watchlist("British semiconductor agreement")

    def test_billion_dollar_phrase(self) -> None:
        assert title_matches_watchlist(
            "President Trump Brings Home Billion Dollar Deals During State Visit to Korea"
        )

    def test_fact_sheet_phrase(self) -> None:
        assert title_matches_watchlist("Fact Sheet: US-Japan Technology Partnership")

    def test_summit_phrase(self) -> None:
        assert title_matches_watchlist("US-Japan Summit Joint Statement")

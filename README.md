# US Tech Prosperity Deal Tracker

A static web dashboard that tracks US bilateral Technology Prosperity Deals (TPDs) with the UK, Japan, South Korea, and future partners.

Scrapes White House fact sheets, Federal Register, Commerce.gov, and USTR.gov to build a structured, hierarchical view of framework agreements and their associated corporate investment commitments.

## Status

**MVP — In Development**

## Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Preview what would be scraped (no API key needed)
make dry-run

# Run full pipeline (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY='sk-ant-...'
make run

# Start frontend dev server
cd frontend && npm install && cd ..
make dev
```

## Architecture

```
Local Pipeline (Python)          GitHub Actions           GitHub Pages
┌───────────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Scrapers (4 sources)  │    │ Build frontend   │    │ React SPA        │
│ → AI Classifier       │    │ → Deploy to      │    │ reads deals.json │
│ → data/deals.json     │ →  │    gh-pages      │ →  │ statically       │
│   (committed)         │    │                  │    │                  │
└───────────────────────┘    └──────────────────┘    └──────────────────┘
```

### Data Sources

| Source | Method | Auth |
|--------|--------|------|
| Federal Register | JSON API | None (free) |
| whitehouse.gov | HTML scraping | None |
| commerce.gov | HTML scraping | None |
| USTR.gov | HTML scraping | None |

### Country Watchlist

| Country | Code | Signed |
|---------|------|--------|
| United Kingdom | GBR | Sept 2025 |
| Japan | JPN | Oct 2025 |
| South Korea | KOR | Oct 2025 |

Adding a new country = one entry in `pipeline/config.py`. All scrapers pick it up automatically.

## CLI Reference

```bash
python pipeline/main.py [OPTIONS]

Options:
  --dry-run          Preview what would be processed (no API key needed)
  --fetch-only       Fetch and cache pages only, skip classification
  --source NAME      Run one scraper: federal_register, whitehouse, commerce, ustr
  --country NAME     Filter to one country: UK, Japan, "South Korea"
  --no-prefilter     Disable keyword pre-filtering
  --full-text        Disable smart truncation
  --model NAME       Override model (use 'premium' for claude-opus-4-5)
  --batch            Submit as batch job (50% cheaper, async)
  --clear-cache      Clear classification cache before running
  --verbose          Enable DEBUG logging
```

## Makefile Targets

```
make run             # Default pipeline (cheapest)
make run-quality     # Premium model
make run-full        # No optimizations
make dry-run         # Preview mode (no API key)
make fetch-only      # Fetch + cache only
make dev             # Frontend dev server
make build           # Production build
make lint            # Ruff + Black check
```

## Cost Optimization

5-layer pipeline minimizes API costs:

1. **Pre-filter** — keyword matching, zero tokens
2. **Truncation** — cap input at ~800 tokens
3. **Model** — claude-3-5-haiku by default
4. **Caching** — content hash, re-runs are free
5. **Batch API** — opt-in 50% discount

## Full Specification

See [CLAUDE.md](CLAUDE.md) for the complete project specification.

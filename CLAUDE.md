# CLAUDE.md — US Tech Prosperity Deal Tracker

> **Master specification for Claude Code.** Contains project prompt, agent definitions, coding rules, and operations runbook.

---

# Part 1: Project Prompt

## Goal

Build a **US Tech Prosperity Deal (TPD) Tracker** — a static web dashboard that tracks US bilateral Technology Prosperity Deals with partner countries.

The US has signed 3 bilateral TPDs:
- **United Kingdom** — Sept 2025
- **Japan** — Oct 2025
- **South Korea** — Oct 2025

Each TPD contains a framework agreement plus dozens of specific corporate investment commitments (e.g., Korean Air $36.2B Boeing purchase, AWS $5B Korea investment).

A local Python pipeline scrapes government sources and classifies deals using Claude AI, outputting `data/deals.json`. The React frontend reads from this static file. No runtime backend in production.

## Data Sources

Four government sources, all free, no auth required:

| Source | Method | What It Covers |
|--------|--------|----------------|
| **Federal Register** | JSON API (`/api/v1/documents.json`) | Executive orders, trade notices, technology agreements |
| **whitehouse.gov** | HTML scraping (fact sheets + articles) | TPD announcements, fact sheets with corporate commitments |
| **commerce.gov** | HTML scraping (fact sheets + press releases) | Commerce Dept technology partnership announcements |
| **USTR.gov** | HTML scraping (fact sheets + press releases) | Trade representative fact sheets and agreements |

All fetched content is cached to disk in 3 layers. Re-runs never re-download already-cached pages.

### Country Watchlist

Adding a new country = one entry in `pipeline/config.py`. All scrapers pick it up automatically.

```python
COUNTRY_WATCHLIST = {
    "UK": {"names": ["United Kingdom", "UK", "Britain", ...], "code": "GBR"},
    "Japan": {"names": ["Japan", "Japanese", ...], "code": "JPN"},
    "South Korea": {"names": ["South Korea", "Korea", "Korean", "ROK", ...], "code": "KOR"},
}
```

## Architecture

### Key Design Decision

**Static site + local scraper pipeline.** The pipeline runs locally on demand, outputs `data/deals.json`, and the file is committed to the repo. GitHub Actions only builds and deploys the frontend — it never runs the pipeline.

```
┌─────────────────────────────────────────────────────┐
│                  LOCAL (dev machine)                │
│                                                     │
│  pipeline/main.py                                   │
│       │                                             │
│       ▼                                             │
│  Scrapers (4 sources)                               │
│       │  ← .cache/pages/ (Layer 1: raw HTML)        │
│       │  ← .cache/extracted/ (Layer 2: text)        │
│       ▼                                             │
│  AI Classifier (Claude API)                         │
│       │  ← .cache/classifications/ (Layer 3)        │
│       ▼                                             │
│  data/deals.json  ←── committed to repo             │
└─────────────────────────────────────────────────────┘
                          │
                    git push
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              GitHub Actions (CI/CD)                 │
│  Build frontend → Deploy to GitHub Pages            │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│        GitHub Pages (production)                    │
│  React SPA reads data/deals.json statically         │
│  No network requests. No backend.                   │
└─────────────────────────────────────────────────────┘
```

### Hierarchical Data Model

Deals are organized hierarchically:
- **Parent TPDs** (`parent_id: null`) — top-level framework agreements per country
- **Child commitments** (`parent_id: "tpd-kor-2025"`) — individual corporate investment deals

### Stack

- **Pipeline:** Python 3.11+, `httpx`, `beautifulsoup4`, `lxml`, `pydantic` v2
- **AI Classification:** Anthropic Claude API (`anthropic` SDK) — `claude-3-5-haiku` default, `claude-opus-4-5` premium
- **Frontend:** React 18 + Vite + Tailwind CSS v4, `recharts`, `lucide-react`, `date-fns`
- **Data contract:** Static `data/deals.json` committed to repo
- **Deployment:** GitHub Pages via `peaceiris/actions-gh-pages@v3`

### Directory Structure

```
us-tpd-tracker/
├── pipeline/
│   ├── main.py              ← CLI entrypoint
│   ├── config.py            ← ALL constants and toggles
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base.py          ← shared BaseScraper with 3-layer caching
│   │   ├── federal_register.py  ← Federal Register JSON API
│   │   ├── whitehouse.py    ← whitehouse.gov HTML scraper
│   │   ├── commerce.py      ← commerce.gov HTML scraper
│   │   └── ustr.py          ← USTR.gov HTML scraper
│   ├── classifier.py        ← AI extraction + two-pass classification
│   ├── cache.py             ← disk cache helpers (url_hash, content_hash)
│   └── models.py            ← Pydantic v2 models (Deal, Meta, etc.)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DealTable.jsx    ← hierarchical accordion (parent TPDs → children)
│   │   │   ├── DealModal.jsx    ← deal detail with source docs
│   │   │   ├── FilterPanel.jsx  ← country, type, status, sector, keyword
│   │   │   ├── Dashboard.jsx    ← charts (value by country, sector breakdown)
│   │   │   └── MVPBanner.jsx    ← shown when processing cap is active
│   │   ├── hooks/
│   │   │   ├── useDeals.js      ← load + derive parent/child hierarchy
│   │   │   └── useFilters.js    ← filter state management
│   │   ├── constants.js         ← colors, enums, labels, formatValue
│   │   ├── App.jsx              ← hash routing (#deals / #dashboard)
│   │   └── main.jsx
│   ├── public/
│   │   ├── 404.html             ← SPA routing fallback
│   │   └── data/                ← sample + real data for dev
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── tests/
│   ├── test_data_validation.py  ← validates deals.json schema + content
│   └── conftest.py
├── data/
│   ├── deals.json               ← pipeline output — COMMITTED
│   ├── deals.sample.json        ← mock data for frontend dev
│   └── deals.raw.json           ← raw scraper output (debug)
├── .github/
│   └── workflows/
│       └── deploy.yml
├── CLAUDE.md
├── Makefile
└── README.md
```

---

# Part 2: Agent Definitions

## Agent: Scraper Engineer

**Trigger:** Any task involving fetching web pages, parsing HTML/JSON, managing the disk cache, or anything in `pipeline/scrapers/` or `pipeline/cache.py`.

**Responsibilities:**
- Implement one scraper per government source (`federal_register.py`, `whitehouse.py`, `commerce.py`, `ustr.py`) using a shared `BaseScraper` class.
- 3-layer caching: raw pages → extracted text → classifications.
- Respect rate limits: 1.5s delay between requests to the same host.
- Use `httpx` + `beautifulsoup4` for all sources (no JS-heavy sites).
- Extract raw deal candidates (title, URL, date, snippet) — no classification yet.
- Return structured `RawDeal` Pydantic objects.

**Scraper Pattern:**
1. **Discover** — paginate through listing/search pages, collect candidate URLs matching country watchlist names + tech/deal keywords.
2. **Fetch** — for each candidate URL, fetch full page content (Layer 1 cache: raw HTML).
3. **Extract** — parse title, headings, body text into clean text (Layer 2 cache: extracted text).
4. **Return** — structured `RawDeal` objects for the classifier.

**Constraints:**
- Never classify or call the AI API — only fetch and parse.
- Log every request: URL, status code, cache hit/miss.
- Set informative `User-Agent` header.
- 429 → exponential backoff starting at 10 seconds.
- All scraper constants (delays, limits, URLs) in `config.py`.

---

## Agent: AI Extraction Analyst

**Trigger:** Any task involving the Anthropic API, prompt engineering, deal classification, or `pipeline/classifier.py`.

**Responsibilities:**
- Accept a `RawDeal` + extracted page text and classify into structured `Deal` objects.
- Two-pass extraction:
  - **Pass 1:** Identify parent TPDs (framework agreements) — country, date, title, signatories, sectors.
  - **Pass 2:** Extract child corporate commitments — parties, dollar value, sector, details.
- Apply 5-layer cost optimization pipeline (see Rule 2).
- Cache classification results to `.cache/classifications/` by content hash.

**Constraints:**
- Use `claude-3-5-haiku` by default. `claude-opus-4-5` only with `--model premium`.
- Never log or print the raw API key.
- `--dry-run` and `--fetch-only` must work without any API key.
- Validate all API responses with Pydantic. Invalid responses → log and skip.
- Never let a single item failure crash the pipeline.

---

## Agent: Frontend Developer

**Trigger:** Any task involving React components, Vite config, Tailwind styling, charts, or the `frontend/` directory.

**Responsibilities:**
- Build the React UI: Deal Table view (hierarchical accordion), Dashboard view (charts), Deal Detail modal.
- URL hash routing: `#deals` (default) / `#dashboard`.
- Shared `<FilterPanel />` (country, type, status, sector, keyword search) across all views.
- `<DealTable />` groups deals by parent TPD with expandable accordion rows.
- Dashboard: total value by country (bar chart), deals by type (pie), sector breakdown.
- Show `<MVPBanner />` when `meta.max_items_cap` is active.

**Constraints:**
- Vite + React 18 + Tailwind CSS v4 only.
- All data from `data/deals.json` (fetched once at app load). Zero network requests in production.
- Colors and enums in `constants.js` — never hardcoded inline.
- Components < 150 lines. Data transforms in `hooks/`, not in components.
- Proper loading, error, and empty states on every view.

---

## Agent: Integration & DevOps

**Trigger:** Any task involving `Makefile`, GitHub Actions, `.gitignore`, `README.md`, env vars, CLI flags, or wiring frontend ↔ data.

**Responsibilities:**
- `Makefile` with all targets, inline comments.
- GitHub Actions workflow: build frontend → deploy to GitHub Pages.
- `public/404.html` for SPA routing on GitHub Pages.
- All CLI flags parsed in `pipeline/main.py`.
- `.gitignore`: caches, `node_modules/`, `.env`, `dist/`, `__pycache__/`.
- Confirm `data/deals.json` is NOT in `.gitignore`.

**Constraints:**
- Never commit or log secrets.
- All constants in `config.py` (Python) or `constants.js` (frontend).
- GitHub Actions does NOT run the pipeline — only frontend build + deploy.
- Output JSON written atomically (write to temp file → rename).
- `VITE_BASE_PATH` must match repo name: `/us-tpd-tracker/`.

---

# Part 3: Rules & Coding Standards

## Rule 1: Processing Cap

`MAX_DEALS_TO_PROCESS` in `config.py` controls whether a processing cap is applied. Currently set to `None` (no cap — all deals processed). If a cap is needed for development, set it to an integer value. When active:
- Pipeline stops after cap is reached.
- Frontend shows `<MVPBanner />` when `meta.max_items_cap` is set.
- `meta` output includes the cap value.
- Console at startup: `"Processing limited to {N} deals"`

## Rule 2: Cost Optimization Pipeline

API cost is a first-class concern. Apply these 5 layers in order, each independently toggleable:

```
Raw Deal Text
     │
     ▼
┌─────────────────────┐
│ Layer 1: Pre-filter  │  --no-prefilter to disable
│ (keyword matching)   │  Skip non-deal content
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Layer 2: Truncation  │  --full-text to disable
│ (smart excerpting)   │  Cap at ~800 tokens input
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Layer 3: Model       │  --model premium to upgrade
│ (haiku by default)   │  claude-3-5-haiku default
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Layer 4: Caching     │  --clear-cache to bypass
│ (skip if seen)       │  100% savings on re-runs
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Layer 5: Batch API   │  --batch to enable
│ (50% discount)       │  Async, lower cost
└──────────┬──────────┘
           │
           ▼
      Anthropic API call
```

All layers ON by default (except Batch which is opt-in). Each layer logs its effect. Cost summary printed at end of run. All parameters in `config.py`.

## Rule 3: API Key Handling

- Read from `os.environ["ANTHROPIC_API_KEY"]` only.
- If missing, print setup instructions and exit with code 1.
- `--dry-run` and `--fetch-only` work WITHOUT an API key.
- Never log/print/write the key value.

## Rule 4: Error Resilience

- **Never let a single deal failure crash the pipeline.** Try/except per item. Log. Continue.
- **Log aggressively.** Every request, parse, API call, cache hit/miss, filter decision.
- **Cache everything.** Re-runs should be fast and cheap.
- **Validate everything.** Invalid API responses → log and skip.
- **Track errors in output.** `meta.errors` array includes every failed/skipped item with source + reason.

## Rule 5: Crawling / Network Ethics

- Minimum 1.5s delay between requests to any single host.
- Set `User-Agent: us-tpd-tracker/1.0 (github.com/praparla/us-tpd-tracker)`.
- 429 → exponential backoff starting at 10 seconds.
- 3-layer disk cache: pages → extracted text → classifications. Re-runs never re-download.

## Rule 6: Static Site Architecture

- **No runtime backend** in production. Zero API calls. All data baked in.
- **`data/deals.json` committed to repo.** Not in `.gitignore`.
- **Pipeline runs locally only.** Never in CI/CD.
- **Base path configurable** via `VITE_BASE_PATH` env var.
- **GitHub Actions** only builds frontend and deploys.

## Rule 7: Python Standards

- Python 3.11+. Type hints on all functions. Pydantic v2. `pathlib.Path`. `logging` module (no bare `print` except startup banners). All constants in `config.py`. Pinned `requirements.txt`.
- All pipeline commands require: `PYTHONPATH=. python3 pipeline/main.py`

## Rule 8: Frontend Standards

- React 18 functional components + hooks. Tailwind CSS v4 only. Colors/enums in `constants.js`. Data transforms in `hooks/`. Components < 150 lines. `lucide-react` icons. Proper loading/error/empty states.

## Rule 9: View Toggle Contract

- All views read from the same `useDeals()` hook, which derives parent/child hierarchy.
- Shared filter state in `App.jsx` (passed as props).
- URL hash routing: `#deals` (default) / `#dashboard`.
- Same `<FilterPanel />` and `<DealModal />` across all views.

## Rule 10: Data Contract

Every pipeline run outputs `data/deals.json` with this shape:

```jsonc
{
  "meta": {
    "generated_at": "2025-01-15T12:00:00Z",
    "deals_scanned": 212,
    "deals_processed": 34,
    "max_items_cap": null,
    "date_range_start": "2025-01-01",
    "date_range_end": "2025-12-31",
    "scraper_version": "1.0.0",
    "countries_tracked": ["GBR", "JPN", "KOR"],
    "sources_scraped": ["federal_register", "whitehouse", "commerce", "ustr"],
    "cost_optimization": {
      "prefilter_enabled": true,
      "prefilter_skipped": 95,
      "truncation_enabled": true,
      "model_used": "claude-3-5-haiku-20241022",
      "cache_hits": 40,
      "new_api_calls": 10,
      "batch_mode": false,
      "estimated_cost_usd": 0.03
    },
    "errors": []
  },
  "items": [
    {
      "id": "tpd-kor-2025",
      "parent_id": null,
      "source_url": "https://whitehouse.gov/...",
      "title": "US-Korea Technology Prosperity Deal",
      "summary": "Bilateral tech partnership signed Oct 29, 2025...",
      "type": "TRADE",
      "status": "ACTIVE",
      "parties": ["United States", "Republic of Korea"],
      "deal_value_usd": 75000000000,
      "country": "KOR",
      "date": "2025-10-29",
      "date_signed": "2025-10-29",
      "tags": ["AI", "6G", "biotech", "defense"],
      "sectors": ["AI", "6G Telecommunications", "Biotech"],
      "signatories": ["President Trump", "Minister Bae Kyung-hoon"],
      "source_documents": [
        {"label": "White House Announcement", "url": "..."},
        {"label": "Fact Sheet", "url": "..."}
      ]
    },
    {
      "id": "tpd-kor-2025-001",
      "parent_id": "tpd-kor-2025",
      "title": "Korean Air Boeing Aircraft Purchase",
      "summary": "Korean Air commits to purchasing 103 Boeing aircraft",
      "type": "BUSINESS",
      "status": "ACTIVE",
      "parties": ["Korean Air", "Boeing"],
      "deal_value_usd": 36200000000,
      "country": "KOR",
      "date": "2025-10-29",
      "tags": ["aviation", "defense"],
      "sectors": ["Aviation & Defense"],
      "commitment_details": "103 aircraft including 777-9s, 787-10s, 737 MAX 10s"
    }
  ]
}
```

Key fields:
- `parent_id` — null for framework TPDs, set for child commitments
- `date_signed` — when the framework was signed
- `sectors` — technology/industry sectors covered
- `signatories` — who signed the agreement
- `source_documents` — links to original government pages
- `commitment_details` — specifics for corporate commitments

## Rule 11: Git & Deployment

- `.gitignore`: `pipeline/.cache/`, `node_modules/`, `.env`, `__pycache__/`, `dist/`, `*.pyc`
- `data/deals.json` NOT in `.gitignore` — committed as data snapshot.
- Never commit API keys.
- **Commit regularly** as work is completed — don't batch up large changes.

## Rule 12: Development Workflow

1. **Data fetching** — `make fetch-only` to scrape and cache pages from all sources.
2. **Inspect cached content** — check `pipeline/.cache/extracted/` for scraped page text.
3. **AI classification** — `make run` with `ANTHROPIC_API_KEY` set. Classifier uses two-pass extraction.
4. **Manual data population** — If no API key, read cached extracted text and build `data/deals.json` manually from fact sheets.
5. **Frontend** — `make dev` to start Vite dev server. Reads from `data/deals.json`.
6. **Deployment** — Push to `main` → GitHub Actions auto-deploys to Pages.

## Rule 13: Testing

Run all tests with:
```bash
PYTHONPATH=. python3 -m pytest tests/ -v
```

Test coverage:
- `--dry-run` works without API key — `make dry-run`
- `data/deals.sample.json` committed with mock entries for frontend dev
- `tests/test_data_validation.py` validates:
  - `deals.json` and `deals.sample.json` conform to Pydantic schema
  - Every child deal references a valid parent
  - All required fields are present and properly typed
  - Country codes match the watchlist
  - Deal values are non-negative when present
  - No duplicate IDs

## Rule 14: Security & Credential Handling

### Never Commit Secrets

**CRITICAL — these must NEVER appear in committed code:**
- `ANTHROPIC_API_KEY` or any other API key
- Personal access tokens
- OAuth tokens or session cookies

### Environment Variables

```bash
# Add to ~/.zshrc — NOT to any file in this repo:
export ANTHROPIC_API_KEY="sk-ant-..."
```

### .gitignore Essentials

```
.env
.env.local
pipeline/.cache/
node_modules/
dist/
__pycache__/
*.pyc
```

---

# Part 4: Operations Runbook

## Quick Start

```bash
# Install Python deps
pip install -r requirements.txt

# Preview what would be scraped (no API key needed)
make dry-run

# Fetch and cache pages (no API key needed)
make fetch-only

# Full pipeline (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY='sk-ant-...'
make run

# Start frontend dev server
cd frontend && npm install && cd ..
make dev
```

## CLI Reference

```bash
PYTHONPATH=. python3 pipeline/main.py [OPTIONS]

Options:
  --dry-run          Preview what would be processed. No network requests.
  --fetch-only       Fetch and cache pages only. No AI classification.
  --source NAME      Run one scraper: federal_register, whitehouse, commerce, ustr
  --country NAME     Filter to one country: UK, Japan, "South Korea"
  --no-prefilter     Disable keyword pre-filtering.
  --full-text        Disable smart truncation (send full text to API).
  --model NAME       Override model. Use 'premium' for claude-opus-4-5.
  --batch            Submit as batch job (50% cheaper, async).
  --collect-batch    Retrieve results from a previous batch job.
  --clear-cache      Clear classification cache before running.
  --verbose          Enable DEBUG logging.
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
make help            # Show all targets
```

## Known Issues

### Node.js Not in PATH
```bash
export PATH="/Users/pranava/local/node/bin:$PATH"
```

### PYTHONPATH Required
All pipeline commands need `PYTHONPATH=.` prefix (no setup.py/pyproject.toml).

---

# Part 5: GitHub Deployment

## Quick Deploy

```bash
git push origin main
# GitHub Actions auto-builds and deploys frontend to GitHub Pages
```

## Deployment Workflow

The `.github/workflows/deploy.yml` workflow:
1. Checks out code
2. Sets up Node.js 20
3. Installs frontend deps (`npm ci`)
4. Copies `data/deals.json` and `data/deals.sample.json` to `frontend/public/data/`
5. Builds frontend with `VITE_BASE_PATH=/us-tpd-tracker/`
6. Deploys `frontend/dist/` to `gh-pages` branch

## Deployment Checklist

- [ ] `data/deals.json` exists and is valid JSON
- [ ] `VITE_BASE_PATH=/us-tpd-tracker/` in workflow
- [ ] Push to `main` → verify Actions tab shows green
- [ ] Test live at `https://praparla.github.io/us-tpd-tracker/`

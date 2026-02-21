# CLAUDE.md — US Tech Prosperity Deal Tracker

> **This is the master specification for Claude Code.** It contains the project prompt, agent definitions, and coding rules in a single file. Place this at the root of your repository.

---

# Part 1: Project Prompt

## Goal

Build a **US Tech Prosperity Deal (TPD) Tracker** — a static web dashboard that monitors, classifies, and displays deals across three categories:

1. **Government / Policy** — Federal tech contracts, legislation, regulatory decisions
2. **Business** — Corporate M&A, partnerships, funding rounds with tech implications
3. **Trade** — US bilateral/multilateral trade agreements with tech components

A local Python pipeline scrapes and classifies deals using an AI API, outputting a single `data/deals.json` file that is committed to the repo. The React frontend reads from this static file — no runtime backend in production. The user triggers a refresh manually by running the pipeline locally.

## Data Sources

> **TBD:** Specific scraping targets to be confirmed. Candidate sources:

- **Government:** [USASpending.gov](https://usaspending.gov), [SAM.gov](https://sam.gov), [Congress.gov](https://congress.gov), White House press releases
- **Business:** [Crunchbase](https://crunchbase.com) (public), [PitchBook](https://pitchbook.com) (if access available), tech news outlets (TechCrunch, Reuters)
- **Trade:** [USTR.gov](https://ustr.gov), [Commerce.gov](https://commerce.gov), Federal Register trade notices

All fetched content is cached to disk. Re-runs never re-download already-cached pages.

## Architecture

### Key Design Decision

**Static site + local scraper pipeline.** The pipeline runs locally on demand, outputs `data/deals.json`, and the file is committed to the repo. GitHub Actions only builds and deploys the frontend — it never runs the pipeline. This keeps hosting free (GitHub Pages) and avoids exposing API keys in CI.

```
┌─────────────────────────────────────────────────────┐
│                  LOCAL (dev machine)                │
│                                                     │
│  pipeline/main.py                                   │
│       │                                             │
│       ▼                                             │
│  Scrapers (gov / biz / trade)                       │
│       │  ← cache/ (disk cache, gitignored)          │
│       ▼                                             │
│  AI Classifier (Claude API)                         │
│       │  ← .cache/classifications/ (gitignored)     │
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

### Stack

- **Scraper / Pipeline:** Python 3.11+, `httpx`, `beautifulsoup4`, `playwright` (JS-heavy sites), `pydantic` v2
- **AI Classification:** Anthropic Claude API (`anthropic` SDK) — cheaper model by default, premium opt-in
- **Frontend:** React 18 + Vite + Tailwind CSS, `recharts`, `lucide-react`, `date-fns`
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
│   │   ├── base.py          ← shared scraper base class
│   │   ├── government.py
│   │   ├── business.py
│   │   └── trade.py
│   ├── classifier.py        ← AI extraction + classification
│   ├── cache.py             ← disk cache helpers
│   └── models.py            ← Pydantic models (Deal, Meta, etc.)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DealTable.jsx
│   │   │   ├── DealModal.jsx
│   │   │   ├── FilterPanel.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── MVPBanner.jsx
│   │   ├── hooks/
│   │   │   ├── useDeals.js
│   │   │   └── useFilters.js
│   │   ├── constants.js     ← colors, enums, labels
│   │   └── App.jsx
│   ├── public/
│   │   └── 404.html         ← SPA routing fallback
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── data/
│   └── deals.json           ← pipeline output — COMMITTED
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
- Implement a scraper per deal category (`government.py`, `business.py`, `trade.py`) using a shared `BaseScraper` class.
- Cache all fetched HTML/JSON to `pipeline/.cache/pages/` keyed by URL hash.
- Respect rate limits: minimum 1–2 second delay between requests to the same host.
- Use `playwright` for JS-rendered sites; `httpx` + `beautifulsoup4` for static sites.
- Extract raw deal candidates (title, URL, date, snippet) — no classification yet.
- Return structured `RawDeal` Pydantic objects.

**Constraints:**
- Never classify or call the AI API — only fetch and parse.
- Log every request: URL, status code, cache hit/miss.
- Respect `robots.txt`. Set informative `User-Agent` header.
- 429 → exponential backoff starting at 10 seconds.
- All scraper constants (delays, limits, URLs) in `config.py`.

**Tools/Libraries:** `httpx`, `beautifulsoup4`, `playwright`, `pydantic` v2, `pathlib`, `logging`

---

## Agent: AI Extraction Analyst

**Trigger:** Any task involving the Anthropic API, prompt engineering, deal classification, or `pipeline/classifier.py`.

**Responsibilities:**
- Accept a `RawDeal` (title + snippet + URL) and classify it into a structured `Deal` object.
- Determine: `type` (GOVERNMENT/BUSINESS/TRADE), `status`, `parties`, `deal_value`, clean `summary`.
- Apply cost optimization pipeline in order (see Rule 2).
- Cache classification results to `pipeline/.cache/classifications/` by content hash.
- Output a `cost_summary` dict included in `meta.cost_optimization`.

**Constraints:**
- Use `claude-haiku-3-5` by default. `claude-opus-4-5` only with `--model premium`.
- Never log or print the raw API key — log `"API key present: ✓"` instead.
- `--dry-run` must work without any API key.
- Validate all API responses with Pydantic. Invalid responses → log and skip.
- Never let a single item failure crash the pipeline.

**Tools/Libraries:** `anthropic` SDK, `pydantic` v2, `hashlib`, `logging`

---

## Agent: Frontend Developer

**Trigger:** Any task involving React components, Vite config, Tailwind styling, charts, or the `frontend/` directory.

**Responsibilities:**
- Build the React UI: Dashboard view, Deal Table view, Deal Detail modal.
- URL hash routing: `#dashboard` / `#deals` (bookmarkable). Default: `#deals`.
- Shared `<FilterPanel />` (type, status, date range, keyword search) across all views.
- `<DealModal />` for deal detail — title, summary, parties, value, source link.
- Dashboard: deal count by type, status breakdown pie/bar chart, timeline trend.
- Show `<MVPBanner />` when `meta.max_items_cap` is active.
- Show "Refresh" button in dev only (auto-detect via `import.meta.env.DEV`).

**Constraints:**
- Vite + React 18 + Tailwind CSS only. No other CSS frameworks.
- All data from `data/deals.json` (fetched once at app load). Zero network requests in production.
- Colors and enums in `constants.js` — never hardcoded inline.
- Components < 150 lines. Data transforms in `hooks/`, not in components.
- Desktop-first, min 1024px. No localStorage/sessionStorage.
- Proper loading, error, and empty states on every view.

**Tools/Libraries:** `react`, `recharts`, `tailwindcss`, `lucide-react`, `date-fns`

---

## Agent: Integration & DevOps

**Trigger:** Any task involving `Makefile`, GitHub Actions, `.gitignore`, `README.md`, env vars, CLI flags, or wiring frontend ↔ data.

**Responsibilities:**
- `Makefile` with all targets listed below, with inline comments.
- GitHub Actions workflow: build frontend → deploy to GitHub Pages.
- `public/404.html` for SPA routing on GitHub Pages.
- README with setup instructions, CLI reference, and cost/usage notes.
- All CLI flags parsed in `pipeline/main.py` (see CLI Reference).
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

## Rule 1: MVP Cap Awareness

> **Any processing cap (`MAX_DEALS_TO_PROCESS` in `config.py`) must be surfaced at every layer.**

- Pipeline stops after cap is reached.
- Frontend shows `<MVPBanner />` when `meta.max_items_cap` is set.
- `meta` output includes the cap value.
- Code comments: `# TODO: Remove cap for production`
- Console at startup: `"⚠️ MVP CAP: Processing limited to {MAX_DEALS} deals"`

## Rule 2: Cost Optimization Pipeline

API cost is a first-class concern. Apply these layers in order, each independently toggleable:

```
Raw Deal Text
     │
     ▼
┌─────────────────────┐
│ Layer 1: Pre-filter  │  --no-prefilter to disable
│ (keyword matching)   │  Skip non-deal content
└──────────┬──────────┘
           │ passes filter
           ▼
┌─────────────────────┐
│ Layer 2: Truncation  │  --full-text to disable
│ (smart excerpting)   │  Cap at 800 tokens input
└──────────┬──────────┘
           │ truncated text
           ▼
┌─────────────────────┐
│ Layer 3: Model       │  --model premium to upgrade
│ (haiku by default)   │  claude-haiku-3-5 default
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Layer 4: Caching     │  --clear-cache to bypass
│ (skip if seen)       │  100% savings on re-runs
└──────────┬──────────┘
           │ cache miss
           ▼
┌─────────────────────┐
│ Layer 5: Batch API   │  --batch to enable
│ (50% discount)       │  Async, lower cost
└──────────┬──────────┘
           │
           ▼
      Anthropic API call
```

- All layers ON by default (except Batch which is opt-in).
- Each layer logs its effect. Cost summary printed at end of run.
- All parameters in `config.py`.

## Rule 3: API Key Handling

- Read from `os.environ["ANTHROPIC_API_KEY"]` only.
- If missing, print setup instructions and exit with code 1.
- `--dry-run` works WITHOUT an API key.
- Never log/print/write the key value. Log `"API key present: ✓"` instead.

## Rule 4: Error Resilience

- **Never let a single deal failure crash the pipeline.** Try/except per item. Log. Continue.
- **Log aggressively.** Every request, parse, API call, cache hit/miss, filter decision.
- **Cache everything.** Re-runs should be fast and cheap.
- **Validate everything.** Invalid API responses → log and skip.
- **Track errors in output.** `meta.errors` array includes every failed/skipped item with source + reason.

## Rule 5: Crawling / Network Ethics

- Minimum 1–2 second delay between requests to any single host.
- Set `User-Agent: us-tpd-tracker/1.0 (github.com/praparla/us-tpd-tracker)`.
- Respect `robots.txt`.
- 429 → exponential backoff starting at 10 seconds.
- Cache all fetched content to disk; re-runs never re-download.

## Rule 6: Static Site Architecture

- **No runtime backend** in production. Zero API calls. All data baked in.
- **`data/deals.json` committed to repo.** Not in `.gitignore`.
- **Pipeline runs locally only.** Never in CI/CD.
- **Refresh button dev-only.** Auto-detect via `import.meta.env.DEV` and hide silently in production.
- **Base path configurable** via `VITE_BASE_PATH` env var.
- **GitHub Actions** only builds frontend and deploys.

## Rule 7: Python Standards

- Python 3.11+. Type hints on all functions. Pydantic v2. `pathlib.Path`. `logging` module (no bare `print` except startup banners). `black` + `ruff`. All constants in `config.py`. Pinned `requirements.txt`.

## Rule 8: Frontend Standards

- React 18 functional components + hooks. Tailwind CSS only. Colors/enums in `constants.js`. Data transforms in `hooks/`. Components < 150 lines. `lucide-react` icons. Proper loading/error/empty states. No localStorage/sessionStorage.

## Rule 9: View Toggle Contract

- All views read from the same `useDeals()` hook.
- Shared filter state in `App.jsx` (passed as props).
- URL hash routing: `#dashboard` / `#deals`. Default: `#deals`.
- Same `<FilterPanel />` and `<DealModal />` across all views.

## Rule 10: Data Contract

Every pipeline run outputs `data/deals.json` with this shape:

```jsonc
{
  "meta": {
    "generated_at": "2025-01-15T12:00:00Z",
    "deals_scanned": 150,
    "deals_processed": 10,
    "max_items_cap": 10,
    "date_range_start": "YYYY-MM-DD",
    "date_range_end": "YYYY-MM-DD",
    "scraper_version": "1.0.0",
    "cost_optimization": {
      "prefilter_enabled": true,
      "prefilter_skipped": 95,
      "truncation_enabled": true,
      "model_used": "claude-haiku-3-5",
      "cache_hits": 40,
      "new_api_calls": 10,
      "batch_mode": false,
      "estimated_cost_usd": 0.03
    },
    "errors": [
      { "source": "https://example.gov/deal/123", "error": "Parse error: missing date field" }
    ]
  },
  "items": [
    {
      "id": "gov-2025-0042",
      "source_id": "USASpending-ABC123",
      "source_url": "https://usaspending.gov/award/ABC123",
      "title": "DARPA AI Infrastructure Contract — Anthropic",
      "summary": "DARPA awarded a $50M contract to Anthropic for AI safety research infrastructure.",
      "type": "GOVERNMENT",           // GOVERNMENT | BUSINESS | TRADE
      "status": "ACTIVE",             // ACTIVE | PENDING | COMPLETED | CANCELLED | REPORTED
      "parties": ["DARPA", "Anthropic"],
      "deal_value_usd": 50000000,     // null if unknown
      "country": "USA",               // primary country; for TRADE: counterparty country
      "date": "2025-01-10",
      "tags": ["AI", "defense", "research"]
    }
  ]
}
```

Frontend handles: empty items → empty state. Missing meta → defaults. Cap active → `<MVPBanner />`. Errors present → visible error note in footer. Cost info → "About this data" collapsible section.

## Rule 11: Git & Deployment

- `.gitignore`: `pipeline/.cache/`, `node_modules/`, `.env`, `__pycache__/`, `dist/`, `*.pyc`
- `data/deals.json` NOT in `.gitignore` — committed as data snapshot.
- Never commit API keys. Never manually edit `gh-pages` branch.

## Rule 12: Development Workflow — BUILD IN THIS ORDER

1. **Data fetching** — verify one source is reachable and parseable (`--fetch-only`).
2. **Raw extraction** — single page, verify `RawDeal` output quality.
3. **Pre-filter & truncation** — verify volume reduction on a sample set.
4. **AI classification** — one deal, iterate on prompt. Start with `claude-haiku-3-5`.
5. **Caching** — verify re-runs skip already-classified deals.
6. **Wire pipeline** — end-to-end with cap enforced. Verify cost summary output.
7. **Frontend** — Deal Table first (simplest), then Dashboard charts, then Detail modal.
8. **Integration** — local dev server + auto-detect refresh button.
9. **Deployment** — GitHub Actions. Verify on GitHub Pages.
10. **Batch API / additional sources** — add last.

**Do not skip ahead. Verify each step independently.**

## Rule 13: Testing

- `--dry-run` works without API key — lists what would be processed.
- `data/deals.sample.json` committed with 5–10 mock entries for frontend dev.
- Classifier prompt testable in isolation: `python pipeline/classifier.py --test`.
- Pre-filter testable with sample text: `python pipeline/classifier.py --test-filter`.

## Rule 14: Security & Credential Handling

### Never Commit Secrets

**CRITICAL — these must NEVER appear in committed code:**
- `ANTHROPIC_API_KEY` or any other API key
- Personal access tokens
- OAuth tokens or session cookies
- Private URLs with embedded credentials

**If you accidentally commit a secret:**
1. **STOP** — do not push
2. Amend the commit: `git commit --amend`
3. Force-push only if not yet pushed: `git push --force-with-lease`
4. If already pushed: **revoke and regenerate immediately**

### Environment Variables

```bash
# Add to ~/.zshrc — NOT to any file in this repo:
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify it's set:
echo "KEY: '$ANTHROPIC_API_KEY'"
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
.claude/settings.local.json
```

### Pre-Commit Secret Scan

```bash
git diff --cached | grep -iE "apikey|password|token|secret|sk-ant"
```

---

# Part 4: Operations Runbook

## Quick Start

```bash
# Step 1: Install Python deps
pip install -r requirements.txt

# Step 2: Install frontend deps
cd frontend && npm install && cd ..

# Step 3: Fetch & classify deals (requires API key)
export ANTHROPIC_API_KEY='sk-ant-...'
make run

# Step 4: Verify output
cat data/deals.json | python -m json.tool | head -50

# Step 5: Preview in browser
make dev
```

## CLI Reference

```bash
python pipeline/main.py [OPTIONS]

Options:
  --dry-run          List what would be fetched/processed. No downloads, no API calls.
  --fetch-only       Fetch and cache pages only. No AI classification.
  --no-prefilter     Disable keyword pre-filtering (process all fetched items).
  --full-text        Disable smart truncation (send full text to API).
  --model [name]     Override default model. Use 'premium' for claude-opus-4-5.
  --batch            Submit as Anthropic batch job (50% cheaper, async).
  --collect-batch    Retrieve results from a previously submitted batch job.
  --clear-cache      Delete all cached classifications before running.
  --source [name]    Run only one scraper: 'government', 'business', or 'trade'.
  --verbose          Enable DEBUG-level logging.
```

## Makefile Targets

```makefile
run:             ## Default — all cost optimizations active (cheapest)
run-quality:     ## Premium model (~10x cost, better extraction quality)
run-full:        ## No optimizations (most thorough, most expensive)
run-batch:       ## Submit batch job (50% cheaper, async)
collect-batch:   ## Collect batch results from previous submission
run-gov:         ## Run government scraper only
run-biz:         ## Run business scraper only
run-trade:       ## Run trade scraper only
dev:             ## Start frontend dev server (Vite)
build:           ## Production frontend build
deploy:          ## Build + push → triggers GitHub Pages deploy
lint:            ## Run ruff + black check on pipeline/
dry-run:         ## Preview what would be processed (no API key needed)
```

## Known Issues & Workarounds

### API Key Not Found

**Symptom:** `KeyError: 'ANTHROPIC_API_KEY'` even though key appears set.

**Fix:**
```bash
echo "KEY: '$ANTHROPIC_API_KEY'"   # Verify it has a value
export ANTHROPIC_API_KEY='sk-ant-...'  # Re-set explicitly
```

### Node.js Not in PATH

**Symptom:** `command not found: npx`

**Fix:**
```bash
which node || mdfind "kMDItemFSName == 'node' && kMDItemKind == 'Unix Executable File'"
export PATH="/path/to/node/bin:$PATH"
```

### Port Conflicts

**Symptom:** Vite says port 5173 is in use.

**Fix:**
```bash
lsof -i :5173
kill <PID>
```

---

# Part 5: GitHub Deployment Runbook

## Quick Deploy

```bash
git add -A && git commit -m "Update deals data"
git push origin main
# GitHub Actions auto-builds and deploys frontend to GitHub Pages
```

## GitHub Actions Workflow (`.github/workflows/deploy.yml`)

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Build
        run: cd frontend && npm run build
        env:
          VITE_BASE_PATH: /us-tpd-tracker/

      - name: Deploy to gh-pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/dist
```

## Common Deployment Issues

| Symptom | Cause | Fix |
|---|---|---|
| Site returns 404 | `VITE_BASE_PATH` mismatch | Confirm it's `/us-tpd-tracker/` |
| Workflow fails silently | Missing write permissions | Set `contents: write` in workflow |
| Build succeeds, site broken | Base path in `vite.config.js` wrong | Check `base` in vite config |
| Actions blocked | Billing or permissions issue | Check repo Actions settings |

## Deployment Checklist

- [ ] `data/deals.json` exists and is valid JSON
- [ ] `VITE_BASE_PATH=/us-tpd-tracker/` in workflow
- [ ] Push to `main` → verify Actions tab shows green
- [ ] Test live at `https://praparla.github.io/us-tpd-tracker/`

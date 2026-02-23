.PHONY: run run-quality run-full run-batch collect-batch dev build deploy lint dry-run help setup-dev

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# === Pipeline targets ===

run: ## Default pipeline run — all cost optimizations active
	PYTHONPATH=. python3 pipeline/main.py

run-quality: ## Premium model (~10x cost, better extraction quality)
	PYTHONPATH=. python3 pipeline/main.py --model premium

run-full: ## No optimizations (most thorough, most expensive)
	PYTHONPATH=. python3 pipeline/main.py --no-prefilter --full-text --model premium

run-batch: ## Submit batch job (50% cheaper, async)
	PYTHONPATH=. python3 pipeline/main.py --batch

collect-batch: ## Collect batch results from previous submission
	PYTHONPATH=. python3 pipeline/main.py --collect-batch

dry-run: ## Preview what would be processed (no API key needed)
	PYTHONPATH=. python3 pipeline/main.py --dry-run

fetch-only: ## Fetch and cache pages only, no classification
	PYTHONPATH=. python3 pipeline/main.py --fetch-only

lint: ## Run ruff + black check on pipeline/
	ruff check pipeline/ && black --check pipeline/

# === Frontend targets ===

setup-dev: ## Copy sample data for frontend development
	@mkdir -p frontend/public/data
	@cp data/deals.sample.json frontend/public/data/deals.sample.json
	@[ -f data/deals.json ] && cp data/deals.json frontend/public/data/deals.json || true
	@echo "Sample data copied to frontend/public/data/"

dev: setup-dev ## Start frontend dev server (Vite)
	cd frontend && npm run dev

build: ## Production frontend build
	mkdir -p frontend/public/data
	cp data/deals.json frontend/public/data/deals.json
	cd frontend && VITE_BASE_PATH=/us-tpd-tracker/ npm run build

deploy: build ## Build + push (triggers GitHub Pages deploy)
	@echo "Push to main to trigger GitHub Pages deploy"

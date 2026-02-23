"""CLI entrypoint for the US Tech Prosperity Deal Tracker pipeline.

Usage:
    python pipeline/main.py [OPTIONS]

See --help for all options.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Type

from pipeline.config import (
    COUNTRY_WATCHLIST,
    DATA_DIR,
    MAX_DEALS_TO_PROCESS,
    SCRAPER_VERSION,
)
from pipeline.models import DealsOutput, ErrorRecord, Meta, RawDeal

logger = logging.getLogger(__name__)


def get_scraper_classes() -> Dict[str, Type]:
    """Lazy import scraper classes to avoid import errors if deps missing."""
    from pipeline.scrapers.federal_register import FederalRegisterScraper
    from pipeline.scrapers.whitehouse import WhiteHouseScraper
    from pipeline.scrapers.commerce import CommerceScraper
    from pipeline.scrapers.ustr import USTRScraper

    return {
        "federal_register": FederalRegisterScraper,
        "whitehouse": WhiteHouseScraper,
        "commerce": CommerceScraper,
        "ustr": USTRScraper,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="US Tech Prosperity Deal Tracker Pipeline",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List what would be fetched/processed. No downloads, no API calls.",
    )
    parser.add_argument(
        "--fetch-only", action="store_true",
        help="Fetch and cache pages only. No AI classification.",
    )
    parser.add_argument(
        "--source",
        choices=["federal_register", "whitehouse", "commerce", "ustr"],
        help="Run only one scraper source.",
    )
    parser.add_argument(
        "--country",
        help="Filter to one country from watchlist (e.g., 'UK', 'Japan', 'South Korea').",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    # Phase 3 flags (parsed now, wired in Phase 3)
    parser.add_argument("--no-prefilter", action="store_true",
                        help="Disable keyword pre-filtering.")
    parser.add_argument("--full-text", action="store_true",
                        help="Disable smart truncation (send full text to API).")
    parser.add_argument("--model", type=str, default=None,
                        help="Override model. Use 'premium' for claude-opus-4-5.")
    parser.add_argument("--batch", action="store_true",
                        help="Submit as batch job (50%% cheaper, async).")
    parser.add_argument("--collect-batch", action="store_true",
                        help="Retrieve results from a previous batch job.")
    parser.add_argument("--clear-cache", action="store_true",
                        help="Delete all cached classifications before running.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    if MAX_DEALS_TO_PROCESS:
        print(f"\u26a0\ufe0f  Processing limited to {MAX_DEALS_TO_PROCESS} deals")

    # Validate country filter
    if args.country and args.country not in COUNTRY_WATCHLIST:
        print(f"Error: Unknown country '{args.country}'.")
        print(f"Available: {', '.join(COUNTRY_WATCHLIST.keys())}")
        sys.exit(1)

    # Select scrapers
    all_scrapers = get_scraper_classes()
    if args.source:
        scraper_classes = {args.source: all_scrapers[args.source]}
    else:
        scraper_classes = all_scrapers

    # Dry run — just list what would happen
    if args.dry_run:
        print("\n--- DRY RUN ---")
        print(f"Sources: {', '.join(scraper_classes.keys())}")
        countries = (
            [args.country] if args.country
            else list(COUNTRY_WATCHLIST.keys())
        )
        print(f"Countries: {', '.join(countries)}")
        if MAX_DEALS_TO_PROCESS:
            print(f"Processing cap: {MAX_DEALS_TO_PROCESS} deals")
        else:
            print("Processing cap: None (all deals)")
        print("\nWould scrape these sources:")
        for name in scraper_classes:
            print(f"  - {name}")
        print("\nNo network requests made. No API calls.")
        return

    # Fetch phase
    all_raw_deals: List[RawDeal] = []
    errors: List[ErrorRecord] = []
    sources_scraped: List[str] = []

    for source_name, scraper_cls in scraper_classes.items():
        scraper = scraper_cls(country_filter=args.country)
        try:
            raw = scraper.scrape()
            all_raw_deals.extend(raw)
            sources_scraped.append(source_name)
            print(f"[{source_name}] Fetched {len(raw)} raw deal candidates")
        except Exception as e:
            logger.error("[%s] Scraper failed: %s", source_name, e)
            errors.append(ErrorRecord(source=source_name, error=str(e)))
        finally:
            scraper.close()

    print(f"\nTotal raw deals fetched: {len(all_raw_deals)}")

    if args.fetch_only:
        print("--fetch-only: Stopping before classification.")
        print("Cached pages are in pipeline/.cache/pages/")
        print("Cached extracted text in pipeline/.cache/extracted/")
        # Still write raw output for inspection
        _write_raw_output(all_raw_deals, errors, sources_scraped, args)
        return

    # === Classification phase ===
    from pipeline.cache import clear_cache as do_clear_cache
    from pipeline.classifier import Classifier
    from pipeline.config import CLASSIFICATION_CACHE_DIR, DEFAULT_MODEL, PREMIUM_MODEL
    from pipeline.models import CostOptimization, Deal, DealsOutput, Meta, SourceDocument
    from pipeline.scrapers.base import _get_extracted_text

    # Clear classification cache if requested
    if args.clear_cache:
        do_clear_cache(CLASSIFICATION_CACHE_DIR)

    # Determine model
    model = DEFAULT_MODEL
    if args.model == "premium":
        model = PREMIUM_MODEL
    elif args.model:
        model = args.model

    classifier = Classifier(
        model=model,
        prefilter_enabled=not args.no_prefilter,
        truncation_enabled=not args.full_text,
        batch_mode=args.batch,
    )

    # Classify deals
    all_deals: List[Deal] = []
    deal_counter = 0
    seen_parent_countries: set = set()
    deals_to_process = all_raw_deals[:MAX_DEALS_TO_PROCESS] if MAX_DEALS_TO_PROCESS else all_raw_deals

    for raw in deals_to_process:
        try:
            # Get the extracted text (cached Layer 2) for this page
            page_text = _get_extracted_text(raw.source_url)
            if not page_text:
                # Fallback: use the snippet from the raw deal
                page_text = f"{raw.title}\n\n{raw.snippet}"

            deal_counter += 1
            parent, children = classifier.classify_page(
                raw, page_text, "tpd", deal_counter,
            )

            if parent:
                # Deduplicate parent TPDs by country
                if parent.country not in seen_parent_countries:
                    all_deals.append(parent)
                    seen_parent_countries.add(parent.country)
                else:
                    # Merge: add source documents to existing parent
                    for existing in all_deals:
                        if existing.parent_id is None and existing.country == parent.country:
                            existing.source_documents.extend(parent.source_documents)
                            break

                # Always add children
                all_deals.extend(children)

        except Exception as e:
            logger.error("Classification failed for '%s': %s", raw.title[:50], e)
            errors.append(ErrorRecord(source=raw.source_url, error=str(e)))

    # Build final output
    countries_tracked = (
        [COUNTRY_WATCHLIST[args.country]["code"]] if args.country
        else [info["code"] for info in COUNTRY_WATCHLIST.values()]
    )

    # Compute cost
    classifier.estimate_cost()

    output = DealsOutput(
        meta=Meta(
            generated_at=datetime.utcnow().isoformat() + "Z",
            deals_scanned=len(all_raw_deals),
            deals_processed=len(all_deals),
            max_items_cap=MAX_DEALS_TO_PROCESS,
            date_range_start="2025-01-01",
            date_range_end=datetime.utcnow().strftime("%Y-%m-%d"),
            scraper_version=SCRAPER_VERSION,
            countries_tracked=countries_tracked,
            sources_scraped=sources_scraped,
            cost_optimization=classifier.stats,
            errors=errors,
        ),
        items=all_deals,
    )

    # Atomic write to data/deals.json
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / "deals.json"
    with tempfile.NamedTemporaryFile(
        mode="w", dir=DATA_DIR, suffix=".tmp", delete=False,
    ) as f:
        f.write(output.model_dump_json(indent=2))
        tmp_path = Path(f.name)
    tmp_path.rename(output_path)

    # Print cost summary
    print(f"\n{'='*50}")
    print(f"  Pipeline Complete")
    print(f"{'='*50}")
    print(f"  Scanned:          {output.meta.deals_scanned}")
    print(f"  Processed:        {output.meta.deals_processed}")
    parents = sum(1 for d in all_deals if d.parent_id is None)
    children = sum(1 for d in all_deals if d.parent_id is not None)
    print(f"  Parent TPDs:      {parents}")
    print(f"  Child commits:    {children}")
    print(f"  Pre-filter skip:  {classifier.stats.prefilter_skipped}")
    print(f"  Cache hits:       {classifier.stats.cache_hits}")
    print(f"  New API calls:    {classifier.stats.new_api_calls}")
    print(f"  Estimated cost:   ${classifier.stats.estimated_cost_usd}")
    print(f"  Output:           {output_path}")
    print(f"{'='*50}")


def _write_raw_output(
    raw_deals: List[RawDeal],
    errors: List[ErrorRecord],
    sources_scraped: List[str],
    args: argparse.Namespace,
) -> None:
    """Write raw (unclassified) deals to a debug output file."""
    countries = (
        [COUNTRY_WATCHLIST[args.country]["code"]] if args.country
        else [info["code"] for info in COUNTRY_WATCHLIST.values()]
    )

    output = {
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "deals_scanned": len(raw_deals),
            "deals_processed": 0,
            "max_items_cap": MAX_DEALS_TO_PROCESS,
            "scraper_version": SCRAPER_VERSION,
            "countries_tracked": countries,
            "sources_scraped": sources_scraped,
            "note": "Raw unclassified output — classification not yet run",
            "errors": [e.model_dump() for e in errors],
        },
        "raw_deals": [d.model_dump() for d in (raw_deals[:MAX_DEALS_TO_PROCESS] if MAX_DEALS_TO_PROCESS else raw_deals)],
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / "deals.raw.json"
    with tempfile.NamedTemporaryFile(
        mode="w", dir=DATA_DIR, suffix=".tmp", delete=False,
    ) as f:
        json.dump(output, f, indent=2)
        tmp_path = Path(f.name)
    tmp_path.rename(output_path)
    print(f"\nRaw output written to: {output_path}")


if __name__ == "__main__":
    main()

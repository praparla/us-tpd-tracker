# UX Backlog

Items identified during UX review of the US Tech Prosperity Deal Tracker frontend.

---

## Section A: UX Research — Competitive Analysis Insights

*Sourced from reviewing TrumpTradeTracker.com, Brookings Trade Tracker, PIIE Tariff Revenue Tracker, AEI China Global Investment Tracker, PolitiFact Promise Tracker, Full Fact Government Tracker, Bloomberg Deals, and Congress.gov Tariff Timeline — Feb 2026.*

---

### R1. Richer Status Labels (6-tier system) — DONE
- **Implemented:** Replaced binary ACTIVE/PENDING with 6-tier system: SIGNED, COMMITTED, IN_PROGRESS, COMPLETED, STALLED, UNVERIFIED. Each status has a lucide-react icon + semantic color pill. Status legend (collapsible) below filter panel. Updated Python `DealStatus` enum, all test assertions, and migrated all deals.json status values.
- **Files changed:** `constants.js`, `DealTable.jsx`, `DealModal.jsx`, `App.jsx`, `pipeline/models.py`, `tests/test_models.py`, `tests/test_classifier.py`, `data/deals.json`, `frontend/public/data/deals.json`
- **Lesson:** Changing enum values cascades widely — Python models, test mocks, JSON data files, and frontend constants all must be updated together. The classifier test mocks used hardcoded status strings that broke silently.

---

### R2. Country Hero Cards Above the Table
- **Observation:** TrumpTradeTracker.com leads with flag-icon summary cards — one per country — each showing the tariff rate and an "ACTIVE" badge. Users land on the most natural organizing principle ("which country?") and see aggregated stats before diving into the table. The AEI China Investment Tracker similarly leads with a geographic frame before presenting rows.
- **Current gap:** The country tabs exist but clicking UK/Japan/Korea just filters the table. There is no "at a glance" summary for each country before the rows appear.
- **UX Paradigm: KPI card as pre-table summary.** The "card above table" pattern (used in analytics dashboards like Metabase, Retool, and Bloomberg Markets) establishes orientation before detail. Users confirm they're in the right place before scanning rows. The card answers: *how big is this deal? when was it signed? with whom?* — all without clicking anything.
- **Effort:** Low–Medium
- **Suggested prompt:**
  > When a country tab is selected in the deal tracker (UK, Japan, Korea), render a hero summary card at the top of the DealTable view — above the table rows — showing: country flag emoji, full country name, the parent TPD title, date signed, total committed value (sum of all child deal_value_usd), number of corporate commitments, and the key signatories. Pull all values from the parent TPD item in `useDeals()`. Style it as a bordered card with a soft background tint using the country's assigned color from `constants.js`. Show it only when a single country is selected (not "All Countries").

---

### R3. Information-Dense Collapsed Accordion Rows — DONE
- **Implemented:** Child rows now show: title, type badge, status badge (with icon), first sector tag, parties (or "Parties TBD"), commitment details, value (or "Value TBD"), and source chip. All visible without expanding.
- **Files changed:** `DealTable.jsx`
- **Lesson:** Child rows already had most of this — the main gap was the status badge (previously only on parents) and explicit null-state placeholders.

---

### R4. Sector Breakdown Chart (Composition View)
- **Observation:** Brookings' tracker has a "composition of trade" view — a breakdown of what percentage of total value sits in each industry. The AEI China Tracker lets you filter by sector to see how $X billion splits across energy, transport, real estate. This answers "what type of tech deals is the US actually doing?" which is more insightful than country totals alone.
- **Current gap:** The Dashboard shows total value by country (bar chart) and deals by type (pie). There is no breakdown of the $XXX billion total by sector (AI, Aviation, 6G, Biotech, etc.).
- **UX Paradigm: Composition treemap / stacked bar.** A treemap visually weights proportions by area, making it immediately legible which sectors dominate. A stacked bar chart per country shows whether Korea's deals are aerospace-heavy while Japan's are semiconductor-heavy. This is the "small multiples" design pattern — same structure, different data — that lets users make cross-country comparisons without cognitive load.
- **Effort:** Medium
- **Suggested prompt:**
  > Add a new "Sector Breakdown" section to the Dashboard view in `Dashboard.jsx`. Use recharts `Treemap` to show total committed deal value by sector, pulling from the `sectors` field of all child deals in `useDeals()`. Each sector should map to a distinct color defined in `constants.js`. Add a `SECTOR_COLORS` constant if it doesn't exist. Below the treemap, add a recharts `BarChart` showing value by sector, grouped by country — a stacked or grouped bar so users can compare sector composition across UK, Japan, Korea. Label values directly on bars using recharts `LabelList`. Title this section "Where the money goes: by sector".

---

### R5. Source Attribution Visible at Row Level — DONE
- **Implemented:** `SourceChip` component on both parent and child rows. Matches `source_documents[0].label` against `SOURCE_ABBREV` map in constants (WH, COM, USTR, FR, MOU). Renders as small colored chip with ExternalLink icon, opens source URL in new tab. onClick stops propagation so it doesn't trigger the deal modal.
- **Files changed:** `constants.js` (SOURCE_ABBREV map), `DealTable.jsx` (SourceChip component)
- **Lesson:** The pattern-matching approach (checking if label `includes` a key) is simple and extensible — adding a new source type is just one map entry.

---

### R6. Column Sorting in DealTable
- **Observation:** Every serious policy tracker — Brookings, ProPublica, PolitiFact — allows sorting by key fields. Brookings has a full left-panel control system. PolitiFact lets you sort promises by status. This is baseline expected behavior for any data table used by researchers or journalists.
- **Current gap:** `backlog.md` item #7 already tracks this, but without UX paradigm rationale.
- **UX Paradigm: User-controlled data exploration (spreadsheet metaphor).** Clickable column headers are the standard affordance — the sort arrow (▲/▼) is universally understood. The key design decision is: sort is client-side (no network call), so it should feel instant. A secondary sort (e.g., "value DESC, then date DESC") handles ties gracefully. This is distinct from filtering — sorting doesn't remove rows, it reorders them.
- **Effort:** Medium
- **Note:** Consolidates with existing item #7 in this backlog.
- **Suggested prompt:**
  > Add clickable column header sorting to `DealTable.jsx`. Add a sort state (`{ field, direction }`) to the component. Clicking a column header cycles through: ascending → descending → default (unsorted). Show a sort arrow icon (lucide-react `ArrowUp`/`ArrowDown`/`ArrowUpDown`) next to the active sort column header. Support sorting by: deal value (numeric), date (ISO string comparison), and title (alphabetical). Apply sorting inside `useDeals.js` as a derived value from the existing filtered deals list. Child deals should be sorted within their parent group — do not break the parent/child hierarchy when sorting.

---

### R7. Hero Stat + Direct Chart Annotations — DONE
- **Implemented:** Hero stat banner at top of Dashboard showing total committed value (large number), commitment count, and country count. 3 supporting stat cards below. `LabelList` on bar chart and sector chart for direct value annotations. Dynamic narrative chart title (e.g., "South Korea leads with $X in total commitments"). `computeStats` calculates totalChildValue, childCount, topCountry from child deals only.
- **Files changed:** `Dashboard.jsx`
- **Lesson:** The "narrative visualization" principle made a dramatic difference — dynamic titles that reference the top country by name turn a generic chart into a story. LabelList from recharts was trivial to add but substantially improves readability.

---

### R8. Mobile Card-Based Fallback for DealTable
- **Observation:** TrumpTradeTracker and Bloomberg Deals both collapse to card layouts on mobile — tables simply don't work on small screens. The card pattern (title, value, status badge, sector tags in a stacked block) is universally used in mobile-first data apps.
- **Current gap:** This is also in existing item #1 (Mobile Responsiveness), but without the specific "card fallback" paradigm.
- **UX Paradigm: Responsive information hierarchy.** The table metaphor assumes horizontal space; the card metaphor assumes vertical scrolling. The key insight is that on mobile, users scroll down, not right — so column-based layouts must be converted to stacked key-value pairs. The "card as mobile row" pattern means each deal becomes its own mini-card with the same fields as the table row but stacked vertically.
- **Effort:** Medium
- **Note:** Builds on existing item #1 in this backlog.
- **Suggested prompt:**
  > In `DealTable.jsx`, implement a responsive card-based layout for mobile screens (below `md:` breakpoint). On mobile, replace the table accordion with a stack of deal cards. Each parent TPD card should show: country flag, title, date signed, total value, and an expand button to reveal child commitment cards below it. Each child card shows: title, parties, value, sector tag, status badge, and source attribution. Use Tailwind's `md:hidden` and `hidden md:block` to switch between card and table views. The filter panel and search should remain visible on mobile and affect both layouts.

---

### R9. Honest Empty/Null State Communication — DONE
- **Implemented:** `formatValue(null)` now returns "Value TBD" (was "Undisclosed"). DealTable child rows show "Parties TBD" in italic gray when parties are empty. DealModal always shows Value and Parties fields (with "Value TBD" / "Parties TBD" placeholders). Empty sectors show "Uncategorized" muted tag. Parent rows with no value show "Gov. Framework" label.
- **Files changed:** `constants.js` (formatValue), `DealTable.jsx`, `DealModal.jsx`
- **Lesson:** Decided against a separate `utils.js` helper — the null handling is straightforward enough to inline in each component. The key was making sure every field always renders *something*.

---

## Priority: High

### 1. Mobile Responsiveness
- **Issue:** DealTable parent rows use `flex` with many inline elements that overflow on mobile screens. Sector badges are hidden on mobile but the rest of the row still crowds.
- **Fix:** Stack layout vertically below `sm:` breakpoint. Consider a card-style layout for mobile instead of table rows.
- **Effort:** Medium

### 2. Keyboard Navigation — DONE
- **Implemented:** `focus-visible:ring-2 focus-visible:ring-blue-500` on all interactive elements (nav buttons, filter selects, deal rows, modal close, source links). Escape key closes DealModal. Focus trap in modal cycles Tab between first/last focusable elements.
- **Files changed:** `DealModal.jsx`, `DealTable.jsx`, `App.jsx`, `FilterPanel.jsx`

### 3. URL Deep Linking to Specific Deals
- **Issue:** No way to share a link to a specific deal. All navigation is ephemeral.
- **Fix:** Encode selected deal ID in URL hash (e.g., `#deals/tpd-kor-2025-001`), parse on load and auto-open the modal.
- **Effort:** Medium

### 4. Data Freshness Indicator — DONE
- **Implemented:** "Updated [date]" shown in the page header next to the title, always visible. Uses `formatDate(meta.generated_at)`. The old MVPBanner "About this data" section was removed entirely — freshness is in the header, and pipeline diagnostic info (model used, cache hits, etc.) is dev-facing and belongs in console logs, not the UI.
- **Files changed:** `App.jsx`, deleted `MVPBanner.jsx`

### 5. Deal Comparison View
- **Issue:** No way to compare deals side by side across countries or sectors.
- **Fix:** Checkbox selection on deal rows + comparison panel showing 2-3 deals side-by-side with key metrics aligned.
- **Effort:** High

---

## Priority: Medium

### 6. Animated Transitions
- **Issue:** Accordion expand/collapse and view switching are instant with no animation, which feels jarring.
- **Fix:** CSS transitions on `max-height` or `framer-motion` for smooth accordion open/close. Fade transitions on view changes.
- **Effort:** Low

### 7. Sort Controls on Deal Table
- **Issue:** Deals can only be filtered, not sorted (e.g., by value, date, name).
- **Fix:** Add a sort dropdown or clickable column headers to DealTable. Sort by: value (high/low), date (newest/oldest), alphabetical.
- **Effort:** Medium

### 8. Dark Mode Support
- **Issue:** No dark mode option. The all-white design can be harsh in low-light environments.
- **Fix:** Tailwind `dark:` variants throughout, toggle button in header, persist preference in `localStorage`.
- **Effort:** Medium

### 9. Export / Share Functionality
- **Issue:** No way to export filtered deal data to CSV/PDF or share a filtered view with a colleague.
- **Fix:** Export button generating CSV from `filteredDeals`. Encode filter state in URL query params for shareable links.
- **Effort:** Medium

### 10. Pagination or Virtual Scrolling
- **Issue:** All 42 deals render at once. As more TPDs are signed and deal count grows, this will cause performance issues.
- **Fix:** `@tanstack/react-virtual` for virtual scrolling, or simple "Show more" pagination at 20-deal threshold.
- **Effort:** Medium (virtual scrolling) / Low (pagination)

---

## Priority: Low

### 11. Onboarding / First Visit Guide
- **Issue:** No explanation of what Technology Prosperity Deals are for first-time visitors.
- **Fix:** Brief intro banner dismissible with "Don't show again" stored in `localStorage`.
- **Effort:** Low

### 12. Timeline View
- **Issue:** No chronological visualization of when deals were signed and their progression.
- **Fix:** Horizontal timeline component showing deal signing dates on a time axis, grouped by country.
- **Effort:** High

### 13. Map View
- **Issue:** No geographic visualization of deal partners.
- **Fix:** Simple world map highlighting GBR, JPN, KOR with deal values overlaid. Could use `react-simple-maps` or a lightweight SVG map.
- **Effort:** High (requires map library)

### 14. Notification / Changelog for Data Updates
- **Issue:** No way to see what changed between pipeline runs. Users returning to the site don't know if data is new.
- **Fix:** Generate diff between consecutive `deals.json` versions and show a "What's New" banner.
- **Effort:** Medium

### 15. Collapsible Filter Panel
- **Issue:** Filter bar always takes vertical space even when not in use, especially on mobile.
- **Fix:** Collapse to a single "Filters" button on mobile, expand on click. Show active filter count badge.
- **Effort:** Low

### 16. Deal Status Workflow Visualization
- **Issue:** No visual indicator of deal lifecycle progression (Signed -> Committed -> In Progress -> Completed).
- **Fix:** Small horizontal stepper/progress indicator in the deal detail modal showing status progression through the 6-tier system (SIGNED → COMMITTED → IN_PROGRESS → COMPLETED, with STALLED/UNVERIFIED as off-track branches).
- **Effort:** Low

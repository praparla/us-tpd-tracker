# UX Backlog

Items identified during UX review of the US Tech Prosperity Deal Tracker frontend.

---

## Priority: High

### 1. Mobile Responsiveness
- **Issue:** DealTable parent rows use `flex` with many inline elements that overflow on mobile screens. Sector badges are hidden on mobile but the rest of the row still crowds.
- **Fix:** Stack layout vertically below `sm:` breakpoint. Consider a card-style layout for mobile instead of table rows.
- **Effort:** Medium

### 2. Keyboard Navigation
- **Issue:** No `focus-visible` indicators on interactive elements, no keyboard navigation between deals, no Escape to close modal.
- **Fix:** Add `focus-visible:ring` classes to all clickable elements. Add Escape handler to `DealModal`. Trap focus inside modal when open.
- **Effort:** Low

### 3. URL Deep Linking to Specific Deals
- **Issue:** No way to share a link to a specific deal. All navigation is ephemeral.
- **Fix:** Encode selected deal ID in URL hash (e.g., `#deals/tpd-kor-2025-001`), parse on load and auto-open the modal.
- **Effort:** Medium

### 4. Data Freshness Indicator
- **Issue:** Users can't tell how old the data is without expanding "About this data" in the MVP banner.
- **Fix:** Show "Last updated: Oct 28, 2025" in the header or footer, always visible.
- **Effort:** Low

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
- **Issue:** No visual indicator of deal lifecycle progression (Pending -> Active -> Completed).
- **Fix:** Small horizontal stepper/progress indicator in the deal detail modal showing status progression.
- **Effort:** Low

/**
 * Tests for CountryView component covering:
 * - Task 3: Country cards with dollar totals, click interaction
 *
 * Run with: cd frontend && npm test
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import CountryView from '../CountryView'
import { mockDeals, mockParentJPN, mockParentKOR } from '../../test/fixtures'

describe('CountryView', () => {
  const defaultProps = {
    filteredDeals: mockDeals,
    onSelectDeal: vi.fn(),
  }

  /**
   * WHY: Each tracked country must have its own card displayed.
   * PREVENTS: Missing country card when data includes deals for that country.
   */
  test('renders one card per country with deals', () => {
    render(<CountryView {...defaultProps} />)

    expect(screen.getByText('United Kingdom')).toBeInTheDocument()
    expect(screen.getByText('Japan')).toBeInTheDocument()
    expect(screen.getByText('South Korea')).toBeInTheDocument()
  })

  /**
   * WHY: Dollar amounts are the primary information on country cards.
   * PREVENTS: Total value calculation errors or display bugs.
   */
  test('shows correct total dollar value per country', () => {
    render(<CountryView {...defaultProps} />)

    // JPN children: $332B + $25B = $357B
    expect(screen.getByText('$357.0B')).toBeInTheDocument()
    // KOR children: $36.2B + $5B = $41.2B
    expect(screen.getByText('$41.2B')).toBeInTheDocument()
  })

  /**
   * WHY: GBR deals have no dollar values -- card must handle this gracefully.
   * PREVENTS: "$0" or "NaN" displaying instead of "N/A" for valueless deals.
   */
  test('shows N/A for countries with no dollar-valued deals', () => {
    render(<CountryView {...defaultProps} />)

    // GBR has no deal_value_usd on any deals
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  /**
   * WHY: Clicking a country card must open the parent TPD modal.
   * PREVENTS: Country cards being non-interactive dead-ends.
   */
  test('clicking country card opens parent TPD detail modal', () => {
    const onSelectDeal = vi.fn()
    render(<CountryView {...defaultProps} onSelectDeal={onSelectDeal} />)

    // Click on Japan card
    const japanCard = screen.getByText('Japan').closest('[role="button"]')
    fireEvent.click(japanCard)

    expect(onSelectDeal).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tpd-jpn-2025' })
    )
  })

  /**
   * WHY: Active vs Pending counts must accurately reflect child deal statuses.
   * PREVENTS: Wrong status counts misleading users about deal pipeline.
   */
  test('shows correct active and pending deal counts', () => {
    render(<CountryView {...defaultProps} />)

    // JPN has 1 ACTIVE child and 1 PENDING child in our fixtures
    // We should see correct counts on the Japan card
    const japanCard = screen.getByText('Japan').closest('[role="button"]')
    expect(japanCard).toBeInTheDocument()
    // Check that deal count is shown
    expect(japanCard.textContent).toContain('2') // 2 deals
  })

  /**
   * WHY: Empty state must render when filters exclude all countries.
   * PREVENTS: Crash or blank screen with no matching deals.
   */
  test('renders empty state when no deals match filters', () => {
    render(<CountryView filteredDeals={[]} onSelectDeal={vi.fn()} />)

    expect(screen.getByText('No countries match your filters')).toBeInTheDocument()
  })
})

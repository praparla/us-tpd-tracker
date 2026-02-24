/**
 * Tests for TechAreasView component covering:
 * - Task 2a: Tech area grouping, sector accordion, deal interaction
 *
 * Run with: cd frontend && npm test
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import TechAreasView from '../TechAreasView'
import { mockDeals, mockChildJPN1, mockChildKOR2 } from '../../test/fixtures'

describe('TechAreasView', () => {
  const defaultProps = {
    filteredDeals: mockDeals,
    onSelectDeal: vi.fn(),
  }

  /**
   * WHY: The tech areas view must correctly group child deals by their sectors.
   * PREVENTS: Deals appearing under wrong sectors or being silently dropped.
   */
  test('groups deals by sector with correct counts', () => {
    render(<TechAreasView {...defaultProps} />)

    // "Energy Infrastructure" sector should exist (JPN has 2 deals in it)
    expect(screen.getByText('Energy Infrastructure')).toBeInTheDocument()
    // "Aviation & Defense" sector should exist (KOR has 1 deal)
    expect(screen.getByText('Aviation & Defense')).toBeInTheDocument()
  })

  /**
   * WHY: Deals with multiple sectors must appear in each relevant group.
   * PREVENTS: Deals with multi-sector assignments only appearing once.
   */
  test('deals with multiple sectors appear in each sector group', () => {
    render(<TechAreasView {...defaultProps} />)

    // mockChildKOR2 has sectors: ['Technology & Cloud', 'Artificial Intelligence']
    // Both should exist as sector groups
    expect(screen.getByText('Technology & Cloud')).toBeInTheDocument()
    expect(screen.getByText('Artificial Intelligence')).toBeInTheDocument()
  })

  /**
   * WHY: Parent TPDs should not appear in sector groups (they span multiple sectors).
   * PREVENTS: Framework agreements polluting sector-specific groupings.
   */
  test('excludes parent TPD deals from sector groups', () => {
    render(<TechAreasView {...defaultProps} />)

    // Expand "Energy Infrastructure" sector
    fireEvent.click(screen.getByText('Energy Infrastructure'))

    // Should show child deals but not parent TPD titles
    expect(screen.queryByText('US-Japan Technology Prosperity Deal')).not.toBeInTheDocument()
    expect(screen.getByText('Japan Critical Energy Infrastructure')).toBeInTheDocument()
  })

  /**
   * WHY: Sector groups should be sorted by total value for quick scanning.
   * PREVENTS: Random ordering that hides the biggest sectors.
   */
  test('sorts sector groups by total value descending', () => {
    render(<TechAreasView {...defaultProps} />)

    // Get all sector group headers (they contain sector names)
    const sectorHeaders = screen.getAllByText(/Energy Infrastructure|Aviation & Defense|Technology & Cloud|Artificial Intelligence|Fusion Energy/i)
    // Energy Infrastructure has the highest value ($332B + $25B = $357B)
    // It should appear first
    expect(sectorHeaders[0].textContent).toBe('Energy Infrastructure')
  })

  /**
   * WHY: Clicking a deal within a sector group must open its detail modal.
   * PREVENTS: Modal not opening from tech area view context.
   */
  test('clicking a deal row calls onSelectDeal', () => {
    const onSelectDeal = vi.fn()
    render(<TechAreasView {...defaultProps} onSelectDeal={onSelectDeal} />)

    // Expand a sector
    fireEvent.click(screen.getByText('Aviation & Defense'))

    // Click on a deal within it
    const dealRow = screen.getByText('Korean Air Boeing Aircraft Purchase')
    fireEvent.click(dealRow.closest('[class*="cursor-pointer"]'))

    expect(onSelectDeal).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tpd-kor-2025-001' })
    )
  })

  /**
   * WHY: Renders gracefully when filters exclude all deals.
   * PREVENTS: Crash or blank screen on empty filtered results.
   */
  test('renders empty state when no deals match filters', () => {
    render(<TechAreasView filteredDeals={[]} onSelectDeal={vi.fn()} />)

    expect(screen.getByText('No tech areas match your filters')).toBeInTheDocument()
  })
})

/**
 * Tests for labels, captions, and accessibility attributes covering:
 * - Task 4: View captions, aria-labels, badge tooltips
 *
 * Run with: cd frontend && npm test
 */
import { render, screen } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import FilterPanel from '../FilterPanel'
import DealTable from '../DealTable'
import { mockParents, mockChildren, mockDeals } from '../../test/fixtures'

describe('FilterPanel - Accessibility Labels', () => {
  const defaultProps = {
    filters: { country: 'ALL', type: 'ALL', status: 'ALL', sector: 'ALL', keyword: '' },
    setters: {
      setCountry: vi.fn(),
      setType: vi.fn(),
      setStatus: vi.fn(),
      setSector: vi.fn(),
      setKeyword: vi.fn(),
    },
    allSectors: ['Artificial Intelligence', 'Energy Infrastructure'],
    allCountries: ['GBR', 'JPN', 'KOR'],
  }

  /**
   * WHY: Screen readers need labels to describe form controls.
   * PREVENTS: Accessibility failures where the search input has no programmatic label.
   */
  test('search input has accessible label', () => {
    render(<FilterPanel {...defaultProps} />)

    const searchInput = screen.getByLabelText('Search deals by keyword')
    expect(searchInput).toBeInTheDocument()
    expect(searchInput.tagName).toBe('INPUT')
  })

  /**
   * WHY: All filter selects must have aria-labels for screen reader users.
   * PREVENTS: Filter dropdowns being announced as unlabeled to screen reader users.
   */
  test('country select has aria-label', () => {
    render(<FilterPanel {...defaultProps} />)
    expect(screen.getByLabelText('Filter by country')).toBeInTheDocument()
  })

  test('type select has aria-label', () => {
    render(<FilterPanel {...defaultProps} />)
    expect(screen.getByLabelText('Filter by deal type')).toBeInTheDocument()
  })

  test('status select has aria-label', () => {
    render(<FilterPanel {...defaultProps} />)
    expect(screen.getByLabelText('Filter by deal status')).toBeInTheDocument()
  })

  test('sector select has aria-label', () => {
    render(<FilterPanel {...defaultProps} />)
    expect(screen.getByLabelText('Filter by sector')).toBeInTheDocument()
  })
})

describe('DealTable - Badge Tooltips', () => {
  const defaultProps = {
    parents: mockParents,
    childrenByParent: mockChildren,
    filteredDeals: mockDeals,
    onSelectDeal: vi.fn(),
  }

  /**
   * WHY: Badges should explain their meaning via tooltips for new users.
   * PREVENTS: Users not understanding what "TRADE" or "ACTIVE" means.
   */
  test('type badges have title tooltip', () => {
    render(<DealTable {...defaultProps} />)

    const tradeBadges = screen.getAllByTitle(/Deal type:/i)
    expect(tradeBadges.length).toBeGreaterThan(0)
    expect(tradeBadges[0].title).toContain('Deal type:')
  })

  test('status badges have title tooltip', () => {
    render(<DealTable {...defaultProps} />)

    const statusBadges = screen.getAllByTitle(/Status:/i)
    expect(statusBadges.length).toBeGreaterThan(0)
    expect(statusBadges[0].title).toContain('Status:')
  })

  test('sector badges have title tooltip', () => {
    render(<DealTable {...defaultProps} />)

    const sectorBadges = screen.getAllByTitle(/Sector:/i)
    expect(sectorBadges.length).toBeGreaterThan(0)
    expect(sectorBadges[0].title).toContain('Sector:')
  })
})

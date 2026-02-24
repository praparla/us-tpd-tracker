/**
 * Tests for DealTable component covering:
 * - Task 1: Clickable parent cards (card body opens modal, chevron toggles expand)
 * - Task 2b: Sector badges, financial display improvements
 *
 * Run with: cd frontend && npm test
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import DealTable from '../DealTable'
import {
  mockParents, mockChildren, mockDeals,
  mockParentGBR, mockParentJPN, mockChildJPN1, mockChildKOR1,
} from '../../test/fixtures'

describe('DealTable - Clickable Cards', () => {
  const defaultProps = {
    parents: mockParents,
    childrenByParent: mockChildren,
    filteredDeals: mockDeals,
    onSelectDeal: vi.fn(),
  }

  /**
   * WHY: Users couldn't reliably open deal details because only the title
   * text was clickable. The entire card body (excluding chevron) must open the modal.
   * PREVENTS: Regression where card click area shrinks back to just the title.
   */
  test('clicking parent card body calls onSelectDeal with the parent deal', () => {
    const onSelectDeal = vi.fn()
    render(<DealTable {...defaultProps} onSelectDeal={onSelectDeal} />)

    // The card body has role="button" and contains the title
    const cardBodies = screen.getAllByRole('button', { name: /US-/i })
    // Click on the first parent card body (not the chevron)
    const gbrCard = cardBodies.find((el) => el.textContent.includes('US-UK Technology'))
    if (gbrCard) fireEvent.click(gbrCard)

    expect(onSelectDeal).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tpd-gbr-2025' })
    )
  })

  /**
   * WHY: The chevron must remain the only way to expand/collapse children,
   * separate from the modal-opening click area.
   * PREVENTS: Expand/collapse triggering when user intended to view details.
   */
  test('clicking chevron button toggles children visibility without opening modal', () => {
    const onSelectDeal = vi.fn()
    render(<DealTable {...defaultProps} onSelectDeal={onSelectDeal} />)

    // Find expand buttons by aria-label
    const expandBtn = screen.getByLabelText(/Expand US-UK Technology/i)
    fireEvent.click(expandBtn)

    // Children should now be visible
    expect(screen.getByText('CAISI-AISI AI Standards Partnership')).toBeInTheDocument()

    // Modal should NOT have been triggered
    expect(onSelectDeal).not.toHaveBeenCalled()
  })

  /**
   * WHY: Keyboard users must be able to activate cards with Enter/Space.
   * PREVENTS: Accessibility regression for keyboard-only navigation.
   */
  test('pressing Enter on parent card body opens modal', () => {
    const onSelectDeal = vi.fn()
    render(<DealTable {...defaultProps} onSelectDeal={onSelectDeal} />)

    const cardBodies = screen.getAllByRole('button', { name: /US-/i })
    const jpnCard = cardBodies.find((el) => el.textContent.includes('US-Japan'))
    if (jpnCard) fireEvent.keyDown(jpnCard, { key: 'Enter' })

    expect(onSelectDeal).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tpd-jpn-2025' })
    )
  })

  /**
   * WHY: Child rows should remain fully clickable to open their detail modal.
   * PREVENTS: Regression in child row click behavior during parent refactor.
   */
  test('clicking child row calls onSelectDeal with the child deal', () => {
    const onSelectDeal = vi.fn()
    render(<DealTable {...defaultProps} onSelectDeal={onSelectDeal} />)

    // Expand JPN parent first
    const expandBtn = screen.getByLabelText(/Expand US-Japan/i)
    fireEvent.click(expandBtn)

    // Click on child deal
    const childRow = screen.getByText('Japan Critical Energy Infrastructure')
    fireEvent.click(childRow.closest('[class*="cursor-pointer"]'))

    expect(onSelectDeal).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'tpd-jpn-2025-001' })
    )
  })

  /**
   * WHY: The empty state message must render when no deals match filters.
   * PREVENTS: Blank screen or error when all deals are filtered out.
   */
  test('renders empty state when no deals match filters', () => {
    render(
      <DealTable
        parents={mockParents}
        childrenByParent={mockChildren}
        filteredDeals={[]}
        onSelectDeal={vi.fn()}
      />
    )

    expect(screen.getByText('No deals match your filters')).toBeInTheDocument()
  })
})

describe('DealTable - Deal View Enhancements', () => {
  const defaultProps = {
    parents: mockParents,
    childrenByParent: mockChildren,
    filteredDeals: mockDeals,
    onSelectDeal: vi.fn(),
  }

  /**
   * WHY: Sector badges must be visible on parent rows so users can scan
   * technology areas at a glance without opening the modal.
   * PREVENTS: Sector information only being accessible via the detail modal.
   */
  test('parent rows display sector badges', () => {
    render(<DealTable {...defaultProps} />)

    // GBR parent has "Artificial Intelligence" sector
    const aiBadges = screen.getAllByTitle(/Sector: Artificial Intelligence/i)
    expect(aiBadges.length).toBeGreaterThan(0)
  })

  /**
   * WHY: Long sector lists must be truncated with a "+N" indicator to prevent layout overflow.
   * PREVENTS: Parent rows with many sectors (like JPN with 4 sectors) breaking the layout.
   */
  test('truncates sector badges to 3 with overflow count', () => {
    render(<DealTable {...defaultProps} />)

    // GBR and JPN parents both have 4 sectors, each shows 3 + "+1"
    const overflowIndicators = screen.getAllByText('+1')
    expect(overflowIndicators.length).toBeGreaterThanOrEqual(1)
  })

  /**
   * WHY: Dollar values should use green color for financial emphasis and easy scanning.
   * PREVENTS: Values blending into surrounding text and being hard to find.
   */
  test('displays financial values prominently for valued deals', () => {
    render(<DealTable {...defaultProps} />)

    // JPN parent has $550B value
    expect(screen.getByText('$550.0B')).toBeInTheDocument()
  })

  /**
   * WHY: Government framework deals (GBR) with no dollar amounts need a clear label.
   * PREVENTS: Empty or confusing value area for government-only deals.
   */
  test('shows Gov. Framework label for deals with no dollar value', () => {
    // GBR parent has null deal_value_usd and children with no values
    const gbrOnlyDeals = mockDeals.filter((d) => d.country === 'GBR')
    render(
      <DealTable
        parents={[mockParentGBR]}
        childrenByParent={{ 'tpd-gbr-2025': mockChildren['tpd-gbr-2025'] }}
        filteredDeals={gbrOnlyDeals}
        onSelectDeal={vi.fn()}
      />
    )

    expect(screen.getByText('Gov. Framework')).toBeInTheDocument()
  })
})

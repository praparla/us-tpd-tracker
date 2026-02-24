/**
 * Tests for useSectorGroups hook covering:
 * - Task 2a: Sector grouping data transformation logic
 *
 * Run with: cd frontend && npm test
 */
import { renderHook } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import { useSectorGroups } from '../useSectorGroups'
import { mockDeals, mockChildJPN1, mockChildJPN2, mockChildKOR1, mockChildKOR2 } from '../../test/fixtures'

describe('useSectorGroups', () => {
  /**
   * WHY: Core data transformation logic must be independently testable.
   * PREVENTS: Sector grouping bugs masked by component rendering.
   */
  test('correctly groups deals by sector', () => {
    const { result } = renderHook(() => useSectorGroups(mockDeals))
    const groups = result.current

    // Should have multiple sector groups
    expect(groups.length).toBeGreaterThan(0)

    // "Energy Infrastructure" should have JPN deals
    const energyGroup = groups.find((g) => g.sector === 'Energy Infrastructure')
    expect(energyGroup).toBeDefined()
    expect(energyGroup.dealCount).toBe(2) // mockChildJPN1 + mockChildJPN2
  })

  /**
   * WHY: Value totals per sector must be accurate for the summary display.
   * PREVENTS: Incorrect value calculations misleading users about sector investment.
   */
  test('sums values per sector accurately', () => {
    const { result } = renderHook(() => useSectorGroups(mockDeals))
    const groups = result.current

    const energyGroup = groups.find((g) => g.sector === 'Energy Infrastructure')
    expect(energyGroup.totalValue).toBe(332000000000 + 25000000000)
  })

  /**
   * WHY: Country tracking per sector enables the "across GBR JPN KOR" display.
   * PREVENTS: Missing country flags in sector group headers.
   */
  test('tracks unique countries per sector', () => {
    const { result } = renderHook(() => useSectorGroups(mockDeals))
    const groups = result.current

    const energyGroup = groups.find((g) => g.sector === 'Energy Infrastructure')
    expect(energyGroup.countries).toContain('JPN')
  })

  /**
   * WHY: Empty input must return empty output without crashing.
   * PREVENTS: TypeError when filtered deals list is empty.
   */
  test('returns empty array for empty input', () => {
    const { result } = renderHook(() => useSectorGroups([]))
    expect(result.current).toEqual([])
  })

  /**
   * WHY: Parent TPDs must be excluded (they span multiple sectors).
   * PREVENTS: Framework agreements appearing in sector-specific groups.
   */
  test('excludes parent deals from grouping', () => {
    const { result } = renderHook(() => useSectorGroups(mockDeals))
    const groups = result.current

    // No group should contain a deal without parent_id
    for (const group of groups) {
      for (const deal of group.deals) {
        expect(deal.parent_id).toBeTruthy()
      }
    }
  })
})

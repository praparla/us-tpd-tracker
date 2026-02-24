/**
 * Tests for useCountryStats hook covering:
 * - Task 3: Country aggregation data transformation logic
 *
 * Run with: cd frontend && npm test
 */
import { renderHook } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import { useCountryStats } from '../useCountryStats'
import { mockDeals } from '../../test/fixtures'

describe('useCountryStats', () => {
  /**
   * WHY: Core country aggregation must produce correct stats per country.
   * PREVENTS: Missing countries, wrong parent assignments, or count errors.
   */
  test('correctly aggregates stats per country', () => {
    const { result } = renderHook(() => useCountryStats(mockDeals))
    const stats = result.current

    expect(stats.length).toBe(3) // GBR, JPN, KOR

    const jpn = stats.find((s) => s.code === 'JPN')
    expect(jpn).toBeDefined()
    expect(jpn.parentDeal).toBeDefined()
    expect(jpn.parentDeal.id).toBe('tpd-jpn-2025')
    expect(jpn.dealCount).toBe(2) // 2 JPN children in fixtures
  })

  /**
   * WHY: Countries must be sorted by total value so the biggest partners appear first.
   * PREVENTS: Random ordering that hides the most significant partnerships.
   */
  test('sorts countries by total value descending', () => {
    const { result } = renderHook(() => useCountryStats(mockDeals))
    const stats = result.current

    // JPN has highest child value ($332B + $25B), KOR second ($36.2B + $5B), GBR last ($0)
    expect(stats[0].code).toBe('JPN')
    expect(stats[1].code).toBe('KOR')
    expect(stats[2].code).toBe('GBR')
  })

  /**
   * WHY: Sector tracking enables sector badges on country cards.
   * PREVENTS: Empty sector lists on country cards.
   */
  test('tracks sectors across all children per country', () => {
    const { result } = renderHook(() => useCountryStats(mockDeals))
    const stats = result.current

    const kor = stats.find((s) => s.code === 'KOR')
    expect(kor.sectors).toContain('Aviation & Defense')
    expect(kor.sectors).toContain('Technology & Cloud')
  })

  /**
   * WHY: Empty input must return empty output without crashing.
   * PREVENTS: TypeError when no deals are loaded or all filtered out.
   */
  test('returns empty array for empty deals', () => {
    const { result } = renderHook(() => useCountryStats([]))
    expect(result.current).toEqual([])
  })

  /**
   * WHY: Active/Pending status breakdown must be accurate for the stats grid.
   * PREVENTS: Wrong counts in the Active/Pending badges on country cards.
   */
  test('counts active and pending deals correctly', () => {
    const { result } = renderHook(() => useCountryStats(mockDeals))
    const stats = result.current

    const jpn = stats.find((s) => s.code === 'JPN')
    // mockChildJPN1 is ACTIVE, mockChildJPN2 is PENDING
    expect(jpn.activeCount).toBe(1)
    expect(jpn.pendingCount).toBe(1)
  })
})

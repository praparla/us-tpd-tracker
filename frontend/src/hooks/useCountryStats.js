import { useMemo } from 'react'
import { COUNTRY_INFO } from '../constants'

/**
 * Aggregates deal statistics per country for the Country View tab.
 * Returns sorted array (by total value descending) of country stats.
 */
export function useCountryStats(deals) {
  return useMemo(() => {
    const stats = {}

    for (const deal of deals) {
      const code = deal.country
      if (!stats[code]) {
        stats[code] = {
          code,
          info: COUNTRY_INFO[code] || {},
          parentDeal: null,
          children: [],
          totalValue: 0,
          dealCount: 0,
          sectors: new Set(),
          activeCount: 0,
          pendingCount: 0,
        }
      }

      if (!deal.parent_id) {
        stats[code].parentDeal = deal
      } else {
        stats[code].children.push(deal)
        stats[code].dealCount++
        stats[code].totalValue += deal.deal_value_usd || 0
        for (const s of deal.sectors || []) stats[code].sectors.add(s)
        if (deal.status === 'ACTIVE') stats[code].activeCount++
        if (deal.status === 'PENDING') stats[code].pendingCount++
      }
    }

    return Object.values(stats)
      .map((s) => ({ ...s, sectors: [...s.sectors] }))
      .sort((a, b) => b.totalValue - a.totalValue)
  }, [deals])
}

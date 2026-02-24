import { useMemo } from 'react'

/**
 * Groups child deals by sector for the Tech Areas view.
 * Parent TPDs are excluded since they span multiple sectors.
 * Returns sorted array (by total value descending) of sector groups.
 */
export function useSectorGroups(filteredDeals) {
  return useMemo(() => {
    const sectorMap = {}
    const children = filteredDeals.filter((d) => d.parent_id)

    for (const deal of children) {
      for (const sector of deal.sectors || []) {
        if (!sectorMap[sector]) {
          sectorMap[sector] = { sector, deals: [], totalValue: 0, countries: new Set() }
        }
        sectorMap[sector].deals.push(deal)
        sectorMap[sector].totalValue += deal.deal_value_usd || 0
        sectorMap[sector].countries.add(deal.country)
      }
    }

    return Object.values(sectorMap)
      .map((g) => ({ ...g, countries: [...g.countries], dealCount: g.deals.length }))
      .sort((a, b) => b.totalValue - a.totalValue)
  }, [filteredDeals])
}

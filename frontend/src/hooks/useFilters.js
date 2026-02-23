import { useState, useMemo } from 'react'

export function useFilters(deals) {
  const [country, setCountry] = useState('ALL')
  const [type, setType] = useState('ALL')
  const [status, setStatus] = useState('ALL')
  const [sector, setSector] = useState('ALL')
  const [keyword, setKeyword] = useState('')

  const filteredDeals = useMemo(() => {
    return deals.filter((deal) => {
      if (country !== 'ALL' && deal.country !== country) return false
      if (type !== 'ALL' && deal.type !== type) return false
      if (status !== 'ALL' && deal.status !== status) return false
      if (sector !== 'ALL' && !(deal.sectors || []).includes(sector)) return false
      if (keyword) {
        const kw = keyword.toLowerCase()
        const searchable = `${deal.title} ${deal.summary} ${(deal.parties || []).join(' ')} ${(deal.tags || []).join(' ')}`.toLowerCase()
        if (!searchable.includes(kw)) return false
      }
      return true
    })
  }, [deals, country, type, status, sector, keyword])

  // Derive available sectors from all deals
  const allSectors = useMemo(() => {
    const s = new Set()
    for (const d of deals) {
      for (const sec of d.sectors || []) s.add(sec)
    }
    return [...s].sort()
  }, [deals])

  // Derive available countries from all deals
  const allCountries = useMemo(() => {
    const c = new Set()
    for (const d of deals) {
      if (d.country) c.add(d.country)
    }
    return [...c].sort()
  }, [deals])

  const filters = { country, type, status, sector, keyword }
  const setters = { setCountry, setType, setStatus, setSector, setKeyword }

  return { filteredDeals, filters, setters, allSectors, allCountries }
}

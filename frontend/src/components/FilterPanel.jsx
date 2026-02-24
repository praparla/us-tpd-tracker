import { Search, X } from 'lucide-react'
import { COUNTRY_INFO, DEAL_TYPES, DEAL_STATUSES } from '../constants'

export default function FilterPanel({ filters, setters, allSectors, allCountries }) {
  const { country, type, status, sector, keyword } = filters
  const { setCountry, setType, setStatus, setSector, setKeyword } = setters

  const hasFilters = country !== 'ALL' || type !== 'ALL' || status !== 'ALL' || sector !== 'ALL' || keyword

  function clearAll() {
    setCountry('ALL')
    setType('ALL')
    setStatus('ALL')
    setSector('ALL')
    setKeyword('')
  }

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-gray-200 bg-white p-3">
      {/* Keyword search */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
        <label htmlFor="deal-search" className="sr-only">Search deals</label>
        <input
          id="deal-search"
          type="text"
          placeholder="Search deals..."
          aria-label="Search deals by keyword"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="w-full rounded-md border border-gray-200 bg-gray-50 py-1.5 pl-8 pr-3 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Country */}
      <select
        value={country}
        onChange={(e) => setCountry(e.target.value)}
        aria-label="Filter by country"
        className="rounded-md border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
      >
        <option value="ALL">All Countries</option>
        {allCountries.map((c) => (
          <option key={c} value={c}>
            {COUNTRY_INFO[c]?.flag || ''} {COUNTRY_INFO[c]?.name || c}
          </option>
        ))}
      </select>

      {/* Type */}
      <select
        value={type}
        onChange={(e) => setType(e.target.value)}
        aria-label="Filter by deal type"
        className="rounded-md border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
      >
        <option value="ALL">All Types</option>
        {Object.entries(DEAL_TYPES).map(([k, v]) => (
          <option key={k} value={k}>{v.label}</option>
        ))}
      </select>

      {/* Status */}
      <select
        value={status}
        onChange={(e) => setStatus(e.target.value)}
        aria-label="Filter by deal status"
        className="rounded-md border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
      >
        <option value="ALL">All Statuses</option>
        {Object.entries(DEAL_STATUSES).map(([k, v]) => (
          <option key={k} value={k}>{v.label}</option>
        ))}
      </select>

      {/* Sector */}
      {allSectors.length > 0 && (
        <select
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          aria-label="Filter by sector"
          className="rounded-md border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm outline-none focus:border-blue-500"
        >
          <option value="ALL">All Sectors</option>
          {allSectors.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      )}

      {/* Clear */}
      {hasFilters && (
        <button
          onClick={clearAll}
          className="flex items-center gap-1 rounded-md px-2 py-1.5 text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700"
        >
          <X size={14} /> Clear
        </button>
      )}
    </div>
  )
}

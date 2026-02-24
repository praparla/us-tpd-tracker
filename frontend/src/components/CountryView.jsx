import { COUNTRY_INFO, SECTOR_INFO, formatValue, formatDate } from '../constants'
import { useCountryStats } from '../hooks/useCountryStats'

export default function CountryView({ filteredDeals, onSelectDeal }) {
  const countryStats = useCountryStats(filteredDeals)

  if (countryStats.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white p-12 text-center">
        <p className="text-lg font-medium text-gray-600">No countries match your filters</p>
        <p className="mt-1 text-sm text-gray-400">Try adjusting your search or filter criteria</p>
      </div>
    )
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {countryStats.map((stat) => (
        <CountryCard key={stat.code} stat={stat} onSelectDeal={onSelectDeal} />
      ))}
    </div>
  )
}

function CountryCard({ stat, onSelectDeal }) {
  const { code, info, parentDeal, totalValue, dealCount, sectors, activeCount, pendingCount } = stat

  return (
    <div
      className="cursor-pointer rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-blue-200 hover:shadow-md"
      onClick={() => parentDeal && onSelectDeal(parentDeal)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && parentDeal) onSelectDeal(parentDeal) }}
    >
      {/* Country header */}
      <div className="mb-3 flex items-center gap-3">
        <span className="text-3xl">{info.flag || ''}</span>
        <div>
          <h3 className="text-lg font-bold text-gray-900">{info.name || code}</h3>
          {parentDeal && (
            <p className="text-xs text-gray-500">
              Signed {formatDate(parentDeal.date_signed || parentDeal.date)}
            </p>
          )}
        </div>
      </div>

      {/* Dollar value */}
      <div className="mb-4 rounded-lg bg-green-50 p-3 text-center">
        <p className="mb-0.5 text-xs font-medium text-green-600">Total Committed Investment</p>
        <p className="text-2xl font-bold text-green-700">
          {totalValue > 0 ? formatValue(totalValue) : 'N/A'}
        </p>
      </div>

      {/* Stats grid */}
      <div className="mb-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-lg bg-gray-50 p-2">
          <p className="text-lg font-bold text-gray-900">{dealCount}</p>
          <p className="text-[10px] text-gray-500">Deals</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-2">
          <p className="text-lg font-bold text-green-600">{activeCount}</p>
          <p className="text-[10px] text-gray-500">Active</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-2">
          <p className="text-lg font-bold text-amber-600">{pendingCount}</p>
          <p className="text-[10px] text-gray-500">Pending</p>
        </div>
      </div>

      {/* Sectors */}
      <div className="flex flex-wrap gap-1">
        {sectors.slice(0, 4).map((s) => {
          const si = SECTOR_INFO[s]
          return (
            <span
              key={s}
              className="rounded-full px-2 py-0.5 text-[10px] font-medium"
              style={{ color: si?.color || '#6b7280', backgroundColor: si?.bg || '#f3f4f6' }}
            >
              {s}
            </span>
          )
        })}
        {sectors.length > 4 && (
          <span className="text-[10px] text-gray-400">+{sectors.length - 4}</span>
        )}
      </div>
    </div>
  )
}

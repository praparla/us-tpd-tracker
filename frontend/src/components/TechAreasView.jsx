import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { COUNTRY_INFO, DEAL_TYPES, SECTOR_INFO, formatValue } from '../constants'
import { useSectorGroups } from '../hooks/useSectorGroups'

export default function TechAreasView({ filteredDeals, onSelectDeal, isMobile }) {
  const sectorGroups = useSectorGroups(filteredDeals)
  const [expanded, setExpanded] = useState({})

  function toggleExpand(sector) {
    setExpanded((prev) => ({ ...prev, [sector]: !prev[sector] }))
  }

  if (sectorGroups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white p-8 text-center sm:p-12">
        <p className="text-base font-medium text-gray-600 sm:text-lg">No tech areas match your filters</p>
        <p className="mt-1 text-xs text-gray-400 sm:text-sm">Try adjusting your search or filter criteria</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {sectorGroups.map((group) => {
        const isExpanded = expanded[group.sector]
        const sectorInfo = SECTOR_INFO[group.sector] || {}

        return (
          <div key={group.sector} className="overflow-hidden rounded-lg border border-gray-200 bg-white">
            {/* Sector header */}
            <div
              className="flex cursor-pointer items-center gap-2 p-3 hover:bg-gray-50 sm:gap-3 sm:p-4"
              onClick={() => toggleExpand(group.sector)}
            >
              <button className="flex-shrink-0 text-gray-400">
                {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </button>

              <span
                className="flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold sm:px-2.5 sm:py-1 sm:text-xs"
                style={{ color: sectorInfo.color || '#6b7280', backgroundColor: sectorInfo.bg || '#f3f4f6' }}
              >
                {group.sector}
              </span>

              <div className="min-w-0 flex-1">
                <p className="text-[10px] text-gray-500 sm:text-xs">
                  {group.dealCount} deal{group.dealCount !== 1 ? 's' : ''}{' '}
                  {!isMobile && <>across {group.countries.map((c) => COUNTRY_INFO[c]?.flag || c).join(' ')}</>}
                </p>
              </div>

              <div className="flex-shrink-0 text-right">
                <div className="text-xs font-bold text-green-700 sm:text-sm">
                  {group.totalValue > 0 ? formatValue(group.totalValue) : 'Gov.'}
                </div>
              </div>
            </div>

            {/* Expanded deal list */}
            {isExpanded && (
              <div className="border-t border-gray-100 bg-gray-50/50">
                {group.deals.map((deal) => {
                  const typeInfo = DEAL_TYPES[deal.type]

                  if (isMobile) {
                    return (
                      <div
                        key={deal.id}
                        className="border-b border-gray-100 p-3 last:border-b-0 active:bg-gray-100"
                        onClick={() => onSelectDeal(deal)}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5">
                              <span className="text-sm">{COUNTRY_INFO[deal.country]?.flag || ''}</span>
                              {typeInfo && (
                                <span
                                  className="rounded-full px-1.5 py-0.5 text-[9px] font-medium uppercase"
                                  style={{ color: typeInfo.color, backgroundColor: typeInfo.bg }}
                                >
                                  {typeInfo.label}
                                </span>
                              )}
                            </div>
                            <p className="mt-1 text-sm text-gray-800">{deal.title}</p>
                            <p className="mt-0.5 text-xs text-gray-500">
                              {(deal.parties || []).join(' & ')}
                            </p>
                          </div>
                          <div className="flex-shrink-0 text-right">
                            <div className={`text-sm font-medium ${deal.deal_value_usd ? 'text-green-700' : 'text-gray-400'}`}>
                              {formatValue(deal.deal_value_usd)}
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  }

                  return (
                    <div
                      key={deal.id}
                      className="flex cursor-pointer items-center gap-3 border-b border-gray-100 px-4 py-2.5 pl-12 last:border-b-0 hover:bg-gray-100/50"
                      onClick={() => onSelectDeal(deal)}
                    >
                      <span className="flex-shrink-0 text-base">{COUNTRY_INFO[deal.country]?.flag || ''}</span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-800">{deal.title}</span>
                          {typeInfo && (
                            <span
                              className="flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide"
                              style={{ color: typeInfo.color, backgroundColor: typeInfo.bg }}
                              title={`Deal type: ${typeInfo.label}`}
                            >
                              {typeInfo.label}
                            </span>
                          )}
                        </div>
                        <p className="mt-0.5 truncate text-xs text-gray-500">
                          {(deal.parties || []).join(' & ')}
                        </p>
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <div className={`text-sm font-medium ${deal.deal_value_usd ? 'text-green-700' : 'text-gray-400'}`}>
                          {formatValue(deal.deal_value_usd)}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

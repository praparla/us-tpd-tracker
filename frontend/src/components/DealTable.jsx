import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { COUNTRY_INFO, DEAL_TYPES, DEAL_STATUSES, SECTOR_INFO, formatValue, formatDate } from '../constants'

export default function DealTable({ parents, childrenByParent, filteredDeals, onSelectDeal }) {
  const [expanded, setExpanded] = useState({})

  const filteredParentIds = new Set(filteredDeals.map((d) => d.parent_id || d.id))
  const visibleParents = parents.filter(
    (p) => filteredParentIds.has(p.id) || filteredDeals.some((d) => d.id === p.id)
  )

  function toggleExpand(id) {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  if (visibleParents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white p-12 text-center">
        <p className="text-lg font-medium text-gray-600">No deals match your filters</p>
        <p className="mt-1 text-sm text-gray-400">Try adjusting your search or filter criteria</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {visibleParents.map((parent) => {
        const children = (childrenByParent[parent.id] || []).filter((c) =>
          filteredDeals.some((d) => d.id === c.id)
        )
        const isExpanded = expanded[parent.id]
        const countryInfo = COUNTRY_INFO[parent.country] || {}
        const totalChildValue = children.reduce((sum, c) => sum + (c.deal_value_usd || 0), 0)
        const displayValue = parent.deal_value_usd ?? (totalChildValue > 0 ? totalChildValue : null)

        return (
          <div key={parent.id} className="overflow-hidden rounded-lg border border-gray-200 bg-white">
            {/* Parent row */}
            <div className="flex items-center gap-3 p-4">
              {/* Chevron: only this toggles expand/collapse */}
              <button
                className="flex-shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                onClick={() => toggleExpand(parent.id)}
                aria-expanded={isExpanded}
                aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${parent.title}`}
              >
                {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </button>

              {/* Card body: opens deal detail modal */}
              <div
                className="-m-1 flex min-w-0 flex-1 cursor-pointer items-center gap-3 rounded-md p-1 transition hover:bg-blue-50/50"
                onClick={() => onSelectDeal(parent)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onSelectDeal(parent) }}
              >
                <span className="text-xl">{countryInfo.flag || ''}</span>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <h3 className="truncate text-sm font-semibold text-gray-900">{parent.title}</h3>
                    <TypeBadge type={parent.type} />
                    <StatusBadge status={parent.status} />
                    {parent.sectors?.slice(0, 3).map((s) => (
                      <SectorBadge key={s} sector={s} className="hidden sm:inline-flex" />
                    ))}
                    {parent.sectors?.length > 3 && (
                      <span className="hidden text-[10px] text-gray-400 sm:inline">
                        +{parent.sectors.length - 3}
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 truncate text-xs text-gray-500">{parent.summary}</p>
                </div>

                <div className="min-w-[100px] flex-shrink-0 text-right">
                  {displayValue != null ? (
                    <div className="text-sm font-bold text-green-700">{formatValue(displayValue)}</div>
                  ) : (
                    <div className="text-xs italic text-gray-400">Gov. Framework</div>
                  )}
                  <div className="text-xs text-gray-400">{formatDate(parent.date)}</div>
                </div>

                <div className="flex-shrink-0">
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                    {children.length} commitment{children.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            </div>

            {/* Value composition bar */}
            {isExpanded && totalChildValue > 0 && (
              <div className="flex h-1.5 overflow-hidden bg-gray-100">
                {children
                  .filter((c) => c.deal_value_usd)
                  .map((c) => (
                    <div
                      key={c.id}
                      className="h-full"
                      style={{
                        width: `${(c.deal_value_usd / totalChildValue) * 100}%`,
                        backgroundColor: COUNTRY_INFO[c.country]?.color || '#3b82f6',
                        opacity: 0.6,
                      }}
                      title={`${c.title}: ${formatValue(c.deal_value_usd)}`}
                    />
                  ))}
              </div>
            )}

            {/* Children */}
            {isExpanded && children.length > 0 && (
              <div className="border-t border-gray-100 bg-gray-50/50">
                {children.map((child) => (
                  <div
                    key={child.id}
                    className="flex cursor-pointer items-center gap-3 border-b border-gray-100 px-4 py-2.5 pl-14 last:border-b-0 hover:bg-gray-100/50"
                    onClick={() => onSelectDeal(child)}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-sm text-gray-800">{child.title}</span>
                        <TypeBadge type={child.type} />
                        {child.sectors?.[0] && (
                          <SectorBadge sector={child.sectors[0]} className="hidden sm:inline-flex" />
                        )}
                      </div>
                      <p className="mt-0.5 truncate text-xs text-gray-500">
                        {(child.parties || []).join(' & ')}
                        {child.commitment_details && ` — ${child.commitment_details}`}
                      </p>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <div className={`text-sm font-medium ${child.deal_value_usd ? 'text-green-700' : 'text-gray-400'}`}>
                        {formatValue(child.deal_value_usd)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {isExpanded && children.length === 0 && (
              <div className="border-t border-gray-100 bg-gray-50/50 px-14 py-3 text-xs text-gray-400">
                No child commitments match current filters
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function TypeBadge({ type }) {
  const info = DEAL_TYPES[type]
  if (!info) return null
  return (
    <span
      className="flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide"
      style={{ color: info.color, backgroundColor: info.bg }}
      title={`Deal type: ${info.label}`}
    >
      {info.label}
    </span>
  )
}

function StatusBadge({ status }) {
  const info = DEAL_STATUSES[status]
  if (!info) return null
  return (
    <span
      className="flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide"
      style={{ color: info.color, backgroundColor: info.bg }}
      title={`Status: ${info.label}`}
    >
      {info.label}
    </span>
  )
}

function SectorBadge({ sector, className = '' }) {
  const info = SECTOR_INFO[sector]
  return (
    <span
      className={`flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${className}`}
      style={{ color: info?.color || '#6b7280', backgroundColor: info?.bg || '#f3f4f6' }}
      title={`Sector: ${sector}`}
    >
      {sector}
    </span>
  )
}

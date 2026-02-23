import { useState } from 'react'
import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-react'
import { COUNTRY_INFO, DEAL_TYPES, DEAL_STATUSES, formatValue, formatDate } from '../constants'

export default function DealTable({ parents, childrenByParent, filteredDeals, onSelectDeal }) {
  const [expanded, setExpanded] = useState({})

  // Filter parents to only those matching filters (or having matching children)
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

        return (
          <div key={parent.id} className="overflow-hidden rounded-lg border border-gray-200 bg-white">
            {/* Parent row */}
            <div
              className="flex cursor-pointer items-center gap-3 p-4 hover:bg-gray-50"
              onClick={() => toggleExpand(parent.id)}
            >
              <button className="flex-shrink-0 text-gray-400">
                {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </button>

              <span className="text-xl">{countryInfo.flag || ''}</span>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3
                    className="truncate text-sm font-semibold text-gray-900 hover:text-blue-600"
                    onClick={(e) => { e.stopPropagation(); onSelectDeal(parent) }}
                  >
                    {parent.title}
                  </h3>
                  <TypeBadge type={parent.type} />
                  <StatusBadge status={parent.status} />
                </div>
                <p className="mt-0.5 truncate text-xs text-gray-500">{parent.summary}</p>
              </div>

              <div className="flex-shrink-0 text-right">
                {parent.deal_value_usd != null && (
                  <div className="text-sm font-semibold text-gray-900">{formatValue(parent.deal_value_usd)}</div>
                )}
                {totalChildValue > 0 && parent.deal_value_usd == null && (
                  <div className="text-sm font-semibold text-gray-900">{formatValue(totalChildValue)}</div>
                )}
                <div className="text-xs text-gray-400">{formatDate(parent.date)}</div>
              </div>

              <div className="flex-shrink-0">
                <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                  {children.length} commitment{children.length !== 1 ? 's' : ''}
                </span>
              </div>
            </div>

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
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-800">{child.title}</span>
                        <TypeBadge type={child.type} />
                      </div>
                      <p className="mt-0.5 truncate text-xs text-gray-500">
                        {(child.parties || []).join(' & ')}
                        {child.commitment_details && ` — ${child.commitment_details}`}
                      </p>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <div className="text-sm font-medium text-gray-700">
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
    >
      {info.label}
    </span>
  )
}

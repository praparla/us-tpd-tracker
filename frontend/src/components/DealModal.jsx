import { useEffect, useRef } from 'react'
import { X, ExternalLink, Calendar, Users, DollarSign, Tag, FileText, FileCheck, Handshake, Clock, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react'
import { COUNTRY_INFO, DEAL_TYPES, DEAL_STATUSES, formatValue, formatDate } from '../constants'

const STATUS_ICONS = { FileCheck, Handshake, Clock, CheckCircle2, AlertCircle, HelpCircle }

export default function DealModal({ deal, onClose }) {
  const modalRef = useRef(null)

  // Escape key closes modal
  useEffect(() => {
    if (!deal) return
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [deal, onClose])

  // Focus trap
  useEffect(() => {
    if (!deal || !modalRef.current) return
    const focusable = modalRef.current.querySelectorAll('button, a, [tabindex]:not([tabindex="-1"])')
    if (focusable.length > 0) focusable[0].focus()

    const trapFocus = (e) => {
      if (e.key !== 'Tab' || focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', trapFocus)
    return () => document.removeEventListener('keydown', trapFocus)
  }, [deal])

  if (!deal) return null

  const countryInfo = COUNTRY_INFO[deal.country] || {}
  const typeInfo = DEAL_TYPES[deal.type] || {}
  const statusInfo = DEAL_STATUSES[deal.status] || {}
  const StatusIcon = STATUS_ICONS[statusInfo.icon]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        ref={modalRef}
        className="relative mx-4 max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-gray-200 bg-white p-5">
          <div className="flex-1 pr-4">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-lg">{countryInfo.flag || ''}</span>
              <span
                className="rounded-full px-2 py-0.5 text-xs font-medium"
                style={{ color: typeInfo.color, backgroundColor: typeInfo.bg }}
              >
                {typeInfo.label || deal.type}
              </span>
              <span
                className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
                style={{ color: statusInfo.color, backgroundColor: statusInfo.bg }}
              >
                {StatusIcon && <StatusIcon size={11} />}
                {statusInfo.label || deal.status}
              </span>
            </div>
            <h2 className="text-lg font-semibold text-gray-900">{deal.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="space-y-4 p-5">
          {/* Summary */}
          <p className="text-sm leading-relaxed text-gray-700">{deal.summary}</p>

          {/* Key info grid */}
          <div className="grid grid-cols-2 gap-3">
            <InfoItem
              icon={DollarSign}
              label="Value"
              value={deal.deal_value_usd != null ? formatValue(deal.deal_value_usd) : null}
              placeholder="Value TBD"
            />
            <InfoItem icon={Calendar} label="Date" value={formatDate(deal.date)} />
            {deal.date_signed && (
              <InfoItem icon={Calendar} label="Signed" value={formatDate(deal.date_signed)} />
            )}
            <InfoItem
              icon={Users}
              label="Parties"
              value={deal.parties?.length > 0 ? deal.parties.join(', ') : null}
              placeholder="Parties TBD"
            />
          </div>

          {/* Signatories */}
          {deal.signatories?.length > 0 && (
            <div>
              <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">Signatories</h3>
              <p className="text-sm text-gray-700">{deal.signatories.join(', ')}</p>
            </div>
          )}

          {/* Commitment details */}
          {deal.commitment_details && (
            <div>
              <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">Commitment Details</h3>
              <p className="text-sm text-gray-700">{deal.commitment_details}</p>
            </div>
          )}

          {/* Sectors */}
          <div>
            <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">Sectors</h3>
            {deal.sectors?.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {deal.sectors.map((s) => (
                  <span key={s} className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                    {s}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-xs italic text-gray-400">Uncategorized</span>
            )}
          </div>

          {/* Tags */}
          {deal.tags?.length > 0 && (
            <div>
              <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">Tags</h3>
              <div className="flex flex-wrap gap-1.5">
                {deal.tags.map((t) => (
                  <span key={t} className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-600">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source documents */}
          {deal.source_documents?.length > 0 && (
            <div>
              <h3 className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500">Source Documents</h3>
              <div className="space-y-1">
                {deal.source_documents.map((doc, i) => (
                  <a
                    key={i}
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 hover:underline focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
                  >
                    <FileText size={14} />
                    {doc.label}
                    <ExternalLink size={12} />
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Source URL fallback */}
          {(!deal.source_documents || deal.source_documents.length === 0) && deal.source_url && (
            <a
              href={deal.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 hover:underline focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
            >
              <ExternalLink size={14} />
              View Source
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

function InfoItem({ icon: Icon, label, value, placeholder }) {
  return (
    <div className="rounded-lg bg-gray-50 p-2.5">
      <div className="mb-0.5 flex items-center gap-1 text-xs text-gray-500">
        <Icon size={12} /> {label}
      </div>
      {value ? (
        <div className="text-sm font-medium text-gray-900">{value}</div>
      ) : (
        <div className="text-sm italic text-gray-400">{placeholder || 'TBD'}</div>
      )}
    </div>
  )
}

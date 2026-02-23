import { AlertTriangle, Info, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function MVPBanner({ meta }) {
  const [showCost, setShowCost] = useState(false)

  if (!meta) return null

  const hasCap = meta.max_items_cap != null
  const hasErrors = meta.errors?.length > 0
  const cost = meta.cost_optimization

  return (
    <div className="space-y-2">
      {/* MVP Cap Banner */}
      {hasCap && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          <AlertTriangle size={16} />
          <span>MVP mode: Processing capped at {meta.max_items_cap} deals.</span>
        </div>
      )}

      {/* About this data */}
      <div className="rounded-lg border border-gray-200 bg-white text-sm">
        <button
          onClick={() => setShowCost(!showCost)}
          className="flex w-full items-center justify-between px-4 py-2 text-gray-500 hover:text-gray-700"
        >
          <span className="flex items-center gap-1.5">
            <Info size={14} />
            About this data
          </span>
          {showCost ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {showCost && (
          <div className="border-t border-gray-100 px-4 py-3 text-xs text-gray-500">
            <div className="grid grid-cols-2 gap-x-8 gap-y-1">
              <span>Generated:</span>
              <span>{meta.generated_at ? new Date(meta.generated_at).toLocaleString() : 'N/A'}</span>
              <span>Scanned:</span>
              <span>{meta.deals_scanned ?? 'N/A'} candidates</span>
              <span>Processed:</span>
              <span>{meta.deals_processed ?? 'N/A'} deals</span>
              <span>Sources:</span>
              <span>{(meta.sources_scraped || []).join(', ') || 'N/A'}</span>
              {cost && (
                <>
                  <span>Model:</span>
                  <span>{cost.model_used}</span>
                  <span>Pre-filter skipped:</span>
                  <span>{cost.prefilter_skipped}</span>
                  <span>Cache hits:</span>
                  <span>{cost.cache_hits}</span>
                  <span>API calls:</span>
                  <span>{cost.new_api_calls}</span>
                  <span>Estimated cost:</span>
                  <span>${cost.estimated_cost_usd}</span>
                </>
              )}
            </div>
            {hasErrors && (
              <div className="mt-2 border-t border-gray-100 pt-2">
                <span className="font-medium text-amber-600">{meta.errors.length} error(s) during processing</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

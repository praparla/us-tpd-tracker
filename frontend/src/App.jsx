import { useState, useEffect } from 'react'
import { RefreshCw, LayoutDashboard, List, Globe, Loader2 } from 'lucide-react'
import { VIEW_CAPTIONS } from './constants'
import { useDeals } from './hooks/useDeals'
import { useFilters } from './hooks/useFilters'
import FilterPanel from './components/FilterPanel'
import DealTable from './components/DealTable'
import DealModal from './components/DealModal'
import Dashboard from './components/Dashboard'
import CountryView from './components/CountryView'
import TechAreasView from './components/TechAreasView'
import MVPBanner from './components/MVPBanner'

function getView() {
  const hash = window.location.hash.replace('#', '') || 'deals'
  if (hash === 'dashboard') return 'dashboard'
  if (hash === 'countries') return 'countries'
  return 'deals'
}

export default function App() {
  const { deals, parents, childrenByParent, meta, loading, error, refresh } = useDeals()
  const { filteredDeals, filters, setters, allSectors, allCountries } = useFilters(deals)
  const [view, setView] = useState(getView)
  const [selectedDeal, setSelectedDeal] = useState(null)
  const [dealSubView, setDealSubView] = useState('byDeal')

  useEffect(() => {
    const onHash = () => setView(getView())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  function navigate(v) {
    window.location.hash = v
    setView(v)
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="animate-spin text-blue-500" size={32} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm font-medium text-red-800">Failed to load deals data</p>
          <p className="mt-1 text-xs text-red-600">{error}</p>
          <button
            onClick={refresh}
            className="mt-3 rounded-md bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const caption = VIEW_CAPTIONS[view]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-gray-900">US Tech Prosperity Deal Tracker</h1>
          </div>

          <div className="flex items-center gap-2">
            {/* Nav tabs */}
            <nav className="flex rounded-lg border border-gray-200 bg-gray-50 p-0.5">
              <button
                onClick={() => navigate('deals')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                  view === 'deals'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <List size={15} /> Deals
              </button>
              <button
                onClick={() => navigate('countries')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                  view === 'countries'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Globe size={15} /> Countries
              </button>
              <button
                onClick={() => navigate('dashboard')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                  view === 'dashboard'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <LayoutDashboard size={15} /> Dashboard
              </button>
            </nav>

            {/* Dev-only refresh */}
            {import.meta.env.DEV && (
              <button
                onClick={refresh}
                className="rounded-md border border-gray-200 p-1.5 text-gray-400 hover:bg-gray-50 hover:text-gray-600"
                title="Refresh data (dev only)"
              >
                <RefreshCw size={16} />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl space-y-4 px-4 py-4">
        <MVPBanner meta={meta} />

        <FilterPanel
          filters={filters}
          setters={setters}
          allSectors={allSectors}
          allCountries={allCountries}
        />

        {/* View caption */}
        {caption && (
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-900">{caption.title}</h2>
              <p className="text-xs text-gray-500">{caption.description}</p>
            </div>

            {/* Sub-view toggle for deals */}
            {view === 'deals' && (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-500">Group by:</span>
                <div className="flex rounded-md border border-gray-200 bg-gray-50 p-0.5">
                  <button
                    onClick={() => setDealSubView('byDeal')}
                    className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                      dealSubView === 'byDeal'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    By Deal
                  </button>
                  <button
                    onClick={() => setDealSubView('byTechArea')}
                    className={`rounded px-2.5 py-1 text-xs font-medium transition ${
                      dealSubView === 'byTechArea'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    By Tech Area
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {view === 'deals' ? (
          dealSubView === 'byDeal' ? (
            <DealTable
              parents={parents}
              childrenByParent={childrenByParent}
              filteredDeals={filteredDeals}
              onSelectDeal={setSelectedDeal}
            />
          ) : (
            <TechAreasView filteredDeals={filteredDeals} onSelectDeal={setSelectedDeal} />
          )
        ) : view === 'countries' ? (
          <CountryView filteredDeals={filteredDeals} onSelectDeal={setSelectedDeal} />
        ) : (
          <Dashboard deals={deals} filteredDeals={filteredDeals} meta={meta} />
        )}
      </main>

      {/* Deal detail modal */}
      <DealModal deal={selectedDeal} onClose={() => setSelectedDeal(null)} />
    </div>
  )
}

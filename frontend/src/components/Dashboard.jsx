import { useMemo } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList } from 'recharts'
import { TrendingUp, Globe, Briefcase } from 'lucide-react'
import { COUNTRY_INFO, DEAL_TYPES, CHART_COLORS, formatValue } from '../constants'

export default function Dashboard({ deals, filteredDeals, meta, isMobile }) {
  const stats = useMemo(() => computeStats(filteredDeals), [filteredDeals])

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Hero stat banner */}
      <div className="rounded-xl border border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4 text-center sm:p-6">
        <p className="text-xs font-medium text-gray-500 sm:text-sm">Total Committed Investment</p>
        <p className="mt-1 text-2xl font-bold text-gray-900 sm:text-4xl">{formatValue(stats.totalChildValue)}</p>
        <p className="mt-1 text-[10px] text-gray-500 sm:text-sm">
          across {stats.childCount} commitment{stats.childCount !== 1 ? 's' : ''} in {stats.countryCount} TPD partner countr{stats.countryCount !== 1 ? 'ies' : 'y'}
        </p>
      </div>

      {/* Supporting stat cards */}
      <div className="grid grid-cols-3 gap-2 sm:gap-4">
        <StatCard icon={Briefcase} label="Commitments" value={stats.childCount} color="blue" />
        <StatCard icon={TrendingUp} label="Agreements" value={stats.parentCount} color="green" />
        <StatCard icon={Globe} label="Countries" value={stats.countryCount} color="purple" />
      </div>

      {/* Charts row */}
      <div className="grid gap-3 sm:gap-4 lg:grid-cols-2">
        {/* Value by country */}
        <div className="rounded-lg border border-gray-200 bg-white p-3 sm:p-4">
          <h3 className="mb-0.5 text-xs font-semibold text-gray-700 sm:text-sm">
            {stats.topCountry
              ? `${stats.topCountry} leads in total committed value`
              : 'Deal Value by Country'}
          </h3>
          <p className="mb-2 text-[10px] text-gray-400 sm:mb-3 sm:text-xs">Total committed investment per partner country</p>
          {stats.valueByCountry.length > 0 ? (
            <ResponsiveContainer width="100%" height={isMobile ? 200 : 250}>
              <BarChart data={stats.valueByCountry}>
                <XAxis dataKey="name" tick={{ fontSize: isMobile ? 10 : 12 }} />
                <YAxis tickFormatter={(v) => formatValue(v)} tick={{ fontSize: isMobile ? 9 : 11 }} width={isMobile ? 55 : 70} />
                <Tooltip formatter={(v) => formatValue(v)} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {!isMobile && (
                    <LabelList dataKey="value" position="top" formatter={formatValue} style={{ fontSize: 11, fontWeight: 600, fill: '#374151' }} />
                  )}
                  {stats.valueByCountry.map((entry, i) => (
                    <Cell key={i} fill={COUNTRY_INFO[entry.code]?.color || CHART_COLORS[i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart isMobile={isMobile} />
          )}
        </div>

        {/* Deals by type */}
        <div className="rounded-lg border border-gray-200 bg-white p-3 sm:p-4">
          <h3 className="mb-0.5 text-xs font-semibold text-gray-700 sm:text-sm">Deals by Type</h3>
          <p className="mb-2 text-[10px] text-gray-400 sm:mb-3 sm:text-xs">Distribution of government, business, and trade agreements</p>
          {stats.dealsByType.length > 0 ? (
            <ResponsiveContainer width="100%" height={isMobile ? 200 : 250}>
              <PieChart>
                <Pie
                  data={stats.dealsByType}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={isMobile ? 65 : 90}
                  label={isMobile ? false : ({ name, count }) => `${name} (${count})`}
                  labelLine={false}
                >
                  {stats.dealsByType.map((entry, i) => (
                    <Cell key={i} fill={DEAL_TYPES[entry.type]?.color || CHART_COLORS[i]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart isMobile={isMobile} />
          )}
          {/* Mobile legend for pie chart */}
          {isMobile && stats.dealsByType.length > 0 && (
            <div className="mt-2 flex flex-wrap justify-center gap-3">
              {stats.dealsByType.map((entry, i) => (
                <div key={entry.type} className="flex items-center gap-1 text-[10px] text-gray-600">
                  <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: DEAL_TYPES[entry.type]?.color || CHART_COLORS[i] }} />
                  {entry.name} ({entry.count})
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Sector breakdown */}
      <div className="rounded-lg border border-gray-200 bg-white p-3 sm:p-4">
        <h3 className="mb-0.5 text-xs font-semibold text-gray-700 sm:text-sm">Where the investment goes</h3>
        <p className="mb-2 text-[10px] text-gray-400 sm:mb-3 sm:text-xs">Technology areas with the most deal activity</p>
        {stats.sectorData.length > 0 ? (
          <ResponsiveContainer width="100%" height={isMobile ? Math.min(stats.sectorData.length * 32, 280) : 300}>
            <BarChart data={stats.sectorData} layout="vertical">
              <XAxis type="number" tick={{ fontSize: isMobile ? 9 : 11 }} />
              <YAxis type="category" dataKey="name" width={isMobile ? 110 : 180} tick={{ fontSize: isMobile ? 9 : 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                <LabelList dataKey="count" position="right" style={{ fontSize: isMobile ? 9 : 11, fontWeight: 600, fill: '#374151' }} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart isMobile={isMobile} />
        )}
      </div>
    </div>
  )
}

function computeStats(deals) {
  const totalDeals = deals.length
  const totalValue = deals.reduce((sum, d) => sum + (d.deal_value_usd || 0), 0)
  const countries = new Set(deals.map((d) => d.country))
  const parentCount = deals.filter((d) => !d.parent_id).length
  const children = deals.filter((d) => d.parent_id)
  const childCount = children.length
  const totalChildValue = children.reduce((sum, d) => sum + (d.deal_value_usd || 0), 0)

  // Value by country (child deals only for accurate committed value)
  const countryMap = {}
  for (const d of children) {
    if (!countryMap[d.country]) countryMap[d.country] = 0
    countryMap[d.country] += d.deal_value_usd || 0
  }
  const valueByCountry = Object.entries(countryMap)
    .map(([code, value]) => ({
      code,
      name: COUNTRY_INFO[code]?.short || code,
      value,
    }))
    .sort((a, b) => b.value - a.value)

  const topCountry = valueByCountry.length > 0 ? valueByCountry[0].name : null

  // Deals by type
  const typeMap = {}
  for (const d of deals) {
    typeMap[d.type] = (typeMap[d.type] || 0) + 1
  }
  const dealsByType = Object.entries(typeMap).map(([type, count]) => ({
    type,
    name: DEAL_TYPES[type]?.label || type,
    count,
  }))

  // Sector breakdown
  const sectorMap = {}
  for (const d of deals) {
    for (const s of d.sectors || []) {
      sectorMap[s] = (sectorMap[s] || 0) + 1
    }
  }
  const sectorData = Object.entries(sectorMap)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  return {
    totalDeals,
    totalValue,
    totalChildValue,
    childCount,
    countryCount: countries.size,
    parentCount,
    topCountry,
    valueByCountry,
    dealsByType,
    sectorData,
  }
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    amber: 'bg-amber-50 text-amber-600',
  }
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-2.5 sm:p-4">
      <div className="flex items-center gap-2 sm:gap-3">
        <div className={`rounded-lg p-1.5 sm:p-2 ${colors[color]}`}>
          <Icon size={16} className="sm:h-[18px] sm:w-[18px]" />
        </div>
        <div>
          <p className="text-[10px] text-gray-500 sm:text-xs">{label}</p>
          <p className="text-base font-bold text-gray-900 sm:text-lg">{value}</p>
        </div>
      </div>
    </div>
  )
}

function EmptyChart({ isMobile }) {
  return (
    <div className={`flex items-center justify-center text-sm text-gray-400 ${isMobile ? 'h-[200px]' : 'h-[250px]'}`}>
      No data to display
    </div>
  )
}

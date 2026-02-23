import { useMemo } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { TrendingUp, Globe, Briefcase, DollarSign } from 'lucide-react'
import { COUNTRY_INFO, DEAL_TYPES, CHART_COLORS, formatValue } from '../constants'

export default function Dashboard({ deals, filteredDeals, meta }) {
  const stats = useMemo(() => computeStats(filteredDeals), [filteredDeals])

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={Briefcase} label="Total Deals" value={stats.totalDeals} color="blue" />
        <StatCard icon={DollarSign} label="Total Value" value={formatValue(stats.totalValue)} color="green" />
        <StatCard icon={Globe} label="Countries" value={stats.countryCount} color="purple" />
        <StatCard icon={TrendingUp} label="Parent TPDs" value={stats.parentCount} color="amber" />
      </div>

      {/* Charts row */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Value by country */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">Deal Value by Country</h3>
          {stats.valueByCountry.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={stats.valueByCountry}>
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => formatValue(v)} tick={{ fontSize: 11 }} width={70} />
                <Tooltip formatter={(v) => formatValue(v)} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {stats.valueByCountry.map((entry, i) => (
                    <Cell key={i} fill={COUNTRY_INFO[entry.code]?.color || CHART_COLORS[i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart />
          )}
        </div>

        {/* Deals by type */}
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold text-gray-700">Deals by Type</h3>
          {stats.dealsByType.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={stats.dealsByType}
                  dataKey="count"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={({ name, count }) => `${name} (${count})`}
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
            <EmptyChart />
          )}
        </div>
      </div>

      {/* Sector breakdown */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">Top Sectors</h3>
        {stats.sectorData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.sectorData} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" width={180} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart />
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

  // Value by country
  const countryMap = {}
  for (const d of deals) {
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
    countryCount: countries.size,
    parentCount,
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
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg p-2 ${colors[color]}`}>
          <Icon size={18} />
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-lg font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

function EmptyChart() {
  return (
    <div className="flex h-[250px] items-center justify-center text-sm text-gray-400">
      No data to display
    </div>
  )
}

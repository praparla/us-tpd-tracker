/** Colors, labels, and enums for the US Tech Prosperity Deal Tracker frontend. */

export const COUNTRY_INFO = {
  GBR: { name: 'United Kingdom', flag: '🇬🇧', short: 'UK', color: '#1d4ed8' },
  JPN: { name: 'Japan', flag: '🇯🇵', short: 'Japan', color: '#dc2626' },
  KOR: { name: 'South Korea', flag: '🇰🇷', short: 'S. Korea', color: '#059669' },
  USA: { name: 'United States', flag: '🇺🇸', short: 'US', color: '#7c3aed' },
}

export const DEAL_TYPES = {
  GOVERNMENT: { label: 'Government', color: '#2563eb', bg: '#dbeafe' },
  BUSINESS: { label: 'Business', color: '#059669', bg: '#d1fae5' },
  TRADE: { label: 'Trade', color: '#d97706', bg: '#fef3c7' },
}

export const DEAL_STATUSES = {
  ACTIVE: { label: 'Active', color: '#059669', bg: '#d1fae5' },
  PENDING: { label: 'Pending', color: '#d97706', bg: '#fef3c7' },
  COMPLETED: { label: 'Completed', color: '#6b7280', bg: '#f3f4f6' },
  CANCELLED: { label: 'Cancelled', color: '#dc2626', bg: '#fee2e2' },
  REPORTED: { label: 'Reported', color: '#7c3aed', bg: '#ede9fe' },
}

export const SECTOR_INFO = {
  'Artificial Intelligence': { color: '#7c3aed', bg: '#ede9fe' },
  'Civil Nuclear Energy': { color: '#dc2626', bg: '#fee2e2' },
  'Quantum Computing': { color: '#0891b2', bg: '#cffafe' },
  'Fusion Energy': { color: '#ea580c', bg: '#fff7ed' },
  'Biotechnology': { color: '#16a34a', bg: '#dcfce7' },
  '6G Telecommunications': { color: '#2563eb', bg: '#dbeafe' },
  'Semiconductors': { color: '#9333ea', bg: '#f3e8ff' },
  'Space': { color: '#1e40af', bg: '#dbeafe' },
  'Energy Infrastructure': { color: '#b45309', bg: '#fef3c7' },
  'AI Infrastructure': { color: '#6d28d9', bg: '#ede9fe' },
  'Electronics & Supply Chain': { color: '#0d9488', bg: '#ccfbf1' },
  'Critical Minerals': { color: '#a16207', bg: '#fef9c3' },
  'Manufacturing & Logistics': { color: '#4b5563', bg: '#f3f4f6' },
  'Energy': { color: '#ca8a04', bg: '#fef9c3' },
  'Automotive': { color: '#dc2626', bg: '#fee2e2' },
  'Aviation & Defense': { color: '#1e3a5f', bg: '#e0e7ff' },
  'Technology & Cloud': { color: '#2563eb', bg: '#dbeafe' },
  'Maritime & Shipbuilding': { color: '#0369a1', bg: '#e0f2fe' },
  'Nuclear Energy': { color: '#dc2626', bg: '#fee2e2' },
}

export const VIEW_CAPTIONS = {
  deals: {
    title: 'Technology Prosperity Deals',
    description: 'Browse bilateral framework agreements and corporate investment commitments between the US and partner countries.',
  },
  countries: {
    title: 'Country Overview',
    description: 'Investment totals and deal summaries for each Technology Prosperity Deal partner country.',
  },
  dashboard: {
    title: 'Analytics Dashboard',
    description: 'Aggregate statistics, value breakdowns by country, and sector distribution across all tracked deals.',
  },
}

export const CHART_COLORS = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#0891b2']

export function formatValue(value) {
  if (value == null) return 'Undisclosed'
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(0)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toLocaleString()}`
}

export function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  try {
    const d = new Date(dateStr + 'T00:00:00')
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

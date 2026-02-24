/**
 * Shared test fixtures for frontend component and hook tests.
 * Provides mock deal data matching the data/deals.json contract.
 */

export function createDeal(overrides = {}) {
  return {
    id: 'test-deal-001',
    parent_id: null,
    source_id: '',
    source_url: 'https://www.whitehouse.gov/test',
    title: 'Test Deal',
    summary: 'A test deal summary.',
    type: 'TRADE',
    status: 'ACTIVE',
    parties: ['United States', 'Test Country'],
    deal_value_usd: null,
    country: 'GBR',
    date: '2025-09-18',
    date_signed: '2025-09-18',
    tags: ['AI', 'test'],
    sectors: ['Artificial Intelligence'],
    signatories: ['Test Signatory'],
    source_documents: [],
    commitment_details: null,
    ...overrides,
  }
}

export const mockParentGBR = createDeal({
  id: 'tpd-gbr-2025',
  parent_id: null,
  title: 'US-UK Technology Prosperity Deal',
  summary: 'Bilateral science and technology agreement.',
  type: 'TRADE',
  country: 'GBR',
  sectors: ['Artificial Intelligence', 'Civil Nuclear Energy', 'Quantum Computing', 'Fusion Energy'],
  tags: ['AI', 'quantum', 'nuclear', 'fusion'],
})

export const mockParentJPN = createDeal({
  id: 'tpd-jpn-2025',
  parent_id: null,
  title: 'US-Japan Technology Prosperity Deal',
  summary: 'Comprehensive bilateral tech partnership.',
  type: 'TRADE',
  country: 'JPN',
  deal_value_usd: 550000000000,
  date: '2025-10-28',
  date_signed: '2025-10-28',
  sectors: ['Artificial Intelligence', 'Quantum Computing', 'Biotechnology', 'Energy Infrastructure'],
  tags: ['AI', 'quantum', 'biotech'],
})

export const mockParentKOR = createDeal({
  id: 'tpd-kor-2025',
  parent_id: null,
  title: 'US-Korea Technology Prosperity Deal',
  summary: 'Bilateral technology partnership.',
  type: 'TRADE',
  country: 'KOR',
  deal_value_usd: 71200000000,
  date: '2025-10-29',
  date_signed: '2025-10-29',
  sectors: ['Aviation & Defense', 'Maritime & Shipbuilding', 'Technology & Cloud'],
  tags: ['AI', '6G', 'defense'],
})

export const mockChildGBR1 = createDeal({
  id: 'tpd-gbr-2025-001',
  parent_id: 'tpd-gbr-2025',
  title: 'CAISI-AISI AI Standards Partnership',
  type: 'GOVERNMENT',
  country: 'GBR',
  parties: ['US CAISI', 'UK AISI'],
  sectors: ['Artificial Intelligence'],
  commitment_details: 'Exchange best practices in AI standards.',
})

export const mockChildGBR2 = createDeal({
  id: 'tpd-gbr-2025-002',
  parent_id: 'tpd-gbr-2025',
  title: 'US-UK Fusion Energy R&D Coordination',
  type: 'GOVERNMENT',
  country: 'GBR',
  parties: ['United States', 'United Kingdom'],
  sectors: ['Fusion Energy'],
  commitment_details: 'Coordinate fusion energy R&D.',
})

export const mockChildJPN1 = createDeal({
  id: 'tpd-jpn-2025-001',
  parent_id: 'tpd-jpn-2025',
  title: 'Japan Critical Energy Infrastructure',
  type: 'BUSINESS',
  country: 'JPN',
  deal_value_usd: 332000000000,
  parties: ['Westinghouse', 'GE Vernova', 'Hitachi'],
  sectors: ['Energy Infrastructure'],
  commitment_details: 'Nuclear reactors and power systems.',
})

export const mockChildJPN2 = createDeal({
  id: 'tpd-jpn-2025-002',
  parent_id: 'tpd-jpn-2025',
  title: 'GE Vernova Power Equipment Supply',
  type: 'BUSINESS',
  status: 'PENDING',
  country: 'JPN',
  deal_value_usd: 25000000000,
  parties: ['GE Vernova'],
  sectors: ['Energy Infrastructure'],
  commitment_details: 'Gas turbines and generators.',
})

export const mockChildKOR1 = createDeal({
  id: 'tpd-kor-2025-001',
  parent_id: 'tpd-kor-2025',
  title: 'Korean Air Boeing Aircraft Purchase',
  type: 'BUSINESS',
  country: 'KOR',
  deal_value_usd: 36200000000,
  parties: ['Korean Air', 'Boeing'],
  sectors: ['Aviation & Defense'],
  commitment_details: '103 Boeing aircraft.',
})

export const mockChildKOR2 = createDeal({
  id: 'tpd-kor-2025-002',
  parent_id: 'tpd-kor-2025',
  title: 'Amazon AWS Korea Cloud Investment',
  type: 'BUSINESS',
  country: 'KOR',
  deal_value_usd: 5000000000,
  parties: ['Amazon AWS', 'Republic of Korea'],
  sectors: ['Technology & Cloud', 'Artificial Intelligence'],
  commitment_details: '$5B cloud infrastructure.',
})

export const mockParents = [mockParentGBR, mockParentJPN, mockParentKOR]

export const mockChildren = {
  'tpd-gbr-2025': [mockChildGBR1, mockChildGBR2],
  'tpd-jpn-2025': [mockChildJPN1, mockChildJPN2],
  'tpd-kor-2025': [mockChildKOR1, mockChildKOR2],
}

export const mockDeals = [
  mockParentGBR, mockChildGBR1, mockChildGBR2,
  mockParentJPN, mockChildJPN1, mockChildJPN2,
  mockParentKOR, mockChildKOR1, mockChildKOR2,
]

export const mockMeta = {
  generated_at: '2026-02-23T18:30:00Z',
  deals_scanned: 212,
  deals_processed: 9,
  max_items_cap: null,
  date_range_start: '2025-05-08',
  date_range_end: '2026-02-23',
  scraper_version: '1.0.0',
  countries_tracked: ['GBR', 'JPN', 'KOR'],
  sources_scraped: ['federal_register', 'whitehouse', 'commerce', 'ustr'],
  cost_optimization: {
    prefilter_enabled: true,
    prefilter_skipped: 170,
    truncation_enabled: true,
    model_used: 'manual-extraction',
    cache_hits: 0,
    new_api_calls: 0,
    batch_mode: false,
    estimated_cost_usd: 0.0,
  },
  errors: [],
}

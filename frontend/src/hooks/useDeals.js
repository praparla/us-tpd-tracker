import { useState, useEffect } from 'react'

const DATA_URL = import.meta.env.DEV
  ? '/data/deals.sample.json'
  : `${import.meta.env.BASE_URL}data/deals.json`

export function useDeals() {
  const [deals, setDeals] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    setLoading(true)
    setError(null)

    fetch(DATA_URL)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load deals: ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setMeta(data.meta || null)
        setDeals(data.items || [])
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [refreshKey])

  const refresh = () => setRefreshKey((k) => k + 1)

  // Derive parent/child structure
  const parents = deals.filter((d) => d.parent_id === null || d.parent_id === undefined)
  const childrenByParent = {}
  for (const deal of deals) {
    if (deal.parent_id) {
      if (!childrenByParent[deal.parent_id]) childrenByParent[deal.parent_id] = []
      childrenByParent[deal.parent_id].push(deal)
    }
  }

  return { deals, parents, childrenByParent, meta, loading, error, refresh }
}

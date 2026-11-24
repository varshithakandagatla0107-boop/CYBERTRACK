import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import NetworkGraph from '../components/NetworkGraph'
import { EmptyState, LoadingState, ErrorState } from '../components/States'
import { formatINR } from '../api/client'

export default function NetworkExplorer() {
  const { api } = useAuth()
  const navigate = useNavigate()
  const [graph, setGraph] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [highRiskOnly, setHighRiskOnly] = useState(false)
  const [minAmount, setMinAmount] = useState(0)
  const [selected, setSelected] = useState(null)
  const [ego, setEgo] = useState(null)

  const load = useCallback(async (params = {}) => {
    setLoading(true)
    setError('')
    try {
      const q = new URLSearchParams({
        high_risk_only: String(
          params.highRiskOnly ?? highRiskOnly
        ),
        min_amount: String(
          params.minAmount ?? minAmount
        ),
        limit: '350',
      })
      const g = await api(`/api/network?${q}`)
      setGraph(g)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api, highRiskOnly, minAmount])

  useEffect(() => { load() }, [load])

  const applyFilters = () => load({
    highRiskOnly,
    minAmount: Number(minAmount) || 0,
  })

  const openAccount = async (accountId) => {
    setSelected(accountId)
    try {
      const e = await api(`/api/network/${accountId}`)
      setEgo(e)
    } catch (err) {
      setError(err.message)
    }
  }

  const findShortestPath = async () => {
    const target = prompt('Destination account:')
    if (!target || !selected) return
    try {
      const p = await api(
        `/api/network/${selected}/paths?target=${target.toUpperCase()}`
      )
      if (p.path) {
        setEgo({ ...ego, shortest_path: p })
      } else {
        setError(p.message || 'No path found.')
      }
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <Header
        title="Network Explorer"
        subtitle="Accounts as nodes · transactions as edges"
      >
        <div className="row" style={{ gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <div className="search-input" style={{ width: 220 }}>
            <input
              className="input"
              placeholder="Search account…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && search.trim()) {
                  openAccount(search.trim().toUpperCase())
                }
              }}
            />
          </div>
          {selected && (
            <div className="row" style={{ gap: 8 }}>
              <span className="badge badge-blue">
                Selected: <strong>{selected}</strong>
              </span>
              <button className="btn btn-sm btn-ghost" onClick={() => navigate(`/account/${selected}`)}>
                View Account
              </button>
            </div>
          )}
        </div>
      </Header>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      <div className="card card-pad mb-2">
        <div className="row" style={{ flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
          <label className="row small" style={{ gap: 6 }}>
            <input
              type="checkbox"
              checked={highRiskOnly}
              onChange={(e) =>
                setHighRiskOnly(e.target.checked)
              }
            />
            High-risk only
          </label>
          <div className="field" style={{ width: 170, marginBottom: 0 }}>
            <label>Min amount (₹)</label>
            <input
              className="input"
              type="number"
              min={0}
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
            />
          </div>
          <button className="btn" onClick={applyFilters}>
            Apply filters
          </button>
          {selected && (
            <>
              <button
                className="btn"
                onClick={findShortestPath}
              >
                Shortest money path
              </button>
              <button
                className="btn"
                onClick={() => {
                  setSelected(null)
                  setEgo(null)
                }}
              >
                Clear selection
              </button>
            </>
          )}
          {graph && (
            <span className="small muted" style={{ marginLeft: 'auto' }}>
              {graph.total_nodes} nodes · {graph.total_edges} edges
              {graph.truncated ? ' (truncated)' : ''}
            </span>
          )}
        </div>
      </div>

      {loading && !graph ? (
        <LoadingState label="Building transaction graph…" />
      ) : graph?.nodes?.length === 0 ? (
        <EmptyState
          icon="◎"
          title="No matching transactions"
          desc="Try widening the filters or loading the demonstration case."
          action={
            <button
              className="btn btn-primary"
              onClick={() => load({ highRiskOnly: false, minAmount: 0 })}
            >
              Reset filters
            </button>
          }
        />
      ) : (
        <div className="grid-main">
          <NetworkGraph
            nodes={(ego?.nodes || graph?.nodes)}
            edges={(ego?.edges || graph?.edges)}
            selectedId={selected}
            highlightPath={ego?.shortest_path?.path || []}
            height={560}
            onNodeClick={openAccount}
          />
          <div>
            {selected && ego ? (
              <div className="card card-pad">
                <div className="card-title">
                  Investigation View — {selected}
                </div>
                <div className="grid grid-2">
                  <div className="small">
                    <div className="muted">Neighbours</div>
                    <strong>{ego.neighbour_count}</strong>
                  </div>
                  <div className="small">
                    <div className="muted">Suspicious neighbours</div>
                    <strong>
                      {ego.suspicious_neighbours.length}
                    </strong>
                  </div>
                </div>
                {ego.suspicious_neighbours.length > 0 && (
                  <div className="mt-2">
                    <div className="small muted mb-1">
                      Suspicious neighbours
                    </div>
                    {ego.suspicious_neighbours.map((n) => (
                      <button
                        key={n}
                        className="btn btn-sm btn-ghost"
                        onClick={() => navigate(`/account/${n}`)}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                )}
                {ego.shortest_path && (
                  <div className="mt-2">
                    <div className="small muted mb-1">
                      Shortest money path ({ego.shortest_path.hops} hops)
                    </div>
                    <div className="mono small">
                      {ego.shortest_path.path.join(' → ')}
                    </div>
                  </div>
                )}
                <button
                  className="btn btn-primary mt-2"
                  style={{ width: '100%' }}
                  onClick={() => navigate(`/account/${selected}`)}
                >
                  Open full investigation
                </button>
              </div>
            ) : (
              <>
                <div className="card card-pad mb-2">
                  <div className="card-title">How to read this</div>
                  <ul className="reason-list">
                    <li>Click any node to open its Investigation View.</li>
                    <li>
                      Red nodes are high-risk accounts; amber are medium.
                    </li>
                    <li>
                      Edge thickness reflects transaction value.
                    </li>
                    <li>
                      Red edges connect high-risk accounts.
                    </li>
                    <li>
                      Use "High-risk only" to simplify large graphs.
                    </li>
                  </ul>
                </div>
                <div className="card card-pad">
                  <div className="card-title">Next Steps</div>
                  <div className="grid grid-2">
                    <button
                      className="btn"
                      onClick={() => navigate('/priority')}
                    >
                      View Priority Accounts
                    </button>
                    <button
                      className="btn"
                      onClick={() => navigate('/money-trail')}
                    >
                      Trace Money Trail
                    </button>
                    <button
                      className="btn"
                      onClick={() => navigate('/dashboard')}
                    >
                      Dashboard Overview
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
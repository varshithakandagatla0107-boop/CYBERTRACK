import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import RiskBadge from '../components/RiskBadge'
import DataTable from '../components/DataTable'
import { EmptyState, LoadingState, ErrorState } from '../components/States'
import { formatINR } from '../api/client'

export default function PriorityAccounts() {
  const { api } = useAuth()
  const navigate = useNavigate()
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState('all')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const d = await api('/api/priorities?limit=100')
      setQueue(d.queue || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api])

  useEffect(() => { load() }, [load])

  const filtered = queue.filter((a) => {
    if (filter === 'all') return true
    if (filter === 'high') return a.risk_category === 'high'
    if (filter === 'medium') return a.risk_category === 'medium'
    return true
  })

  const assign = async (accountId) => {
    try {
      const inv = await api('/api/investigations', {
        method: 'POST',
        body: JSON.stringify({
          title: `Priority review — ${accountId}`,
          priority: 'high',
          accounts: [accountId],
          notes: `Assigned from priority queue. Rank reason available in account view.`,
        }),
      })
      navigate(`/investigations/${inv.investigation_id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  const markReviewed = async (accountId) => {
    try {
      await api(
        `/api/accounts/${accountId}/status?status=needs_review`,
        { method: 'PATCH' }
      )
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <Header
        title="Investigation Priority Queue"
        subtitle="Sorted by analytical priority — investigate top-down"
      >
        <div className="row">
          {['all', 'high', 'medium'].map((f) => (
            <button
              key={f}
              className={`btn btn-sm ${filter === f ? 'btn-primary' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'All' : f === 'high' ? 'High' : 'Medium'}
            </button>
          ))}
        </div>
      </Header>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState label="Loading priority queue…" />
      ) : (
        <div className="card">
          <DataTable
            columns={[
              { key: 'rank', label: 'Rank' },
              {
                key: 'account_id', label: 'Account',
                render: (v) => <span className="mono">{v}</span>,
              },
              {
                key: 'risk_score', label: 'Risk',
                render: (v, r) => (
                  <RiskBadge score={v} category={r.risk_category} short />
                ),
              },
              { key: 'network_role', label: 'Network Role' },
              {
                key: 'amount_involved', label: 'Amount Involved',
                className: 'num', render: (v) => formatINR(v),
              },
              {
                key: 'velocity', label: 'Velocity',
                className: 'num',
                render: (v) => `${Number(v).toFixed(1)}/hr`,
              },
              { key: 'reason', label: 'Key Reason',
                render: (v) => (
                  <span className="small">{v}</span>
                ),
              },
              {
                key: 'status', label: 'Status',
                render: (v) => (
                  <span className="badge badge-neutral">{v}</span>
                ),
              },
              {
                key: 'actions', label: 'Actions',
                render: (_, r) => (
                  <div className="row" style={{ gap: 4 }}>
                    <button
                      className="btn btn-sm"
                      onClick={() =>
                        navigate(`/account/${r.account_id}`)
                      }
                    >Investigate</button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => {
                        navigate('/money-trail', {
                          state: { source: r.account_id },
                        })
                      }}
                    >Trace</button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => assign(r.account_id)}
                    >Assign</button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => markReviewed(r.account_id)}
                    >Mark Reviewed</button>
                  </div>
                ),
              },
            ]}
            rows={filtered.map((a) => ({ ...a, id: a.account_id }))}
            emptyMessage="No priority accounts match the filter."
          />
        </div>
      )}

      <div className="disclaimer">
        Priority ordering is an analytical suggestion. The
        investigator decides which account to examine first.
        "Investigate A381 first" is the recommended starting
        point for the demonstration case.
      </div>
    </div>
  )
}

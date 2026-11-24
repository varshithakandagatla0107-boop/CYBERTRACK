import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import NetworkGraph from '../components/NetworkGraph'
import Timeline from '../components/Timeline'
import DataTable from '../components/DataTable'
import { EmptyState, LoadingState } from '../components/States'
import { formatINR, formatDateTime } from '../api/client'

export default function MoneyTrail() {
  const { api } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const preset = location.state?.trail
  const presetSource = location.state?.source

  const [source, setSource] = useState(
    preset?.source_account || presetSource || ''
  )
  const [destination, setDestination] = useState(
    preset?.terminal_account || ''
  )
  const [maxMinutes, setMaxMinutes] = useState(60)
  const [result, setResult] = useState(preset || null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('timeline')
  const [trails, setTrails] = useState([])

  useEffect(() => {
    api('/api/trails').then((d) => setTrails(d.trails || []))
      .catch(() => {})
  }, [api])

  const trace = async () => {
    if (!source.trim()) {
      setError('Source account is required.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const r = await api('/api/trails/trace', {
        method: 'POST',
        body: JSON.stringify({
          source: source.trim().toUpperCase(),
          destination: destination.trim().toUpperCase() || null,
          max_minutes: Number(maxMinutes) || null,
        }),
      })
      setResult(r)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const hops = result?.hops_detail || []
  const path = useMemo(() => {
    if (!hops.length) return []
    const seq = [hops[0].from_account]
    for (const h of hops) seq.push(h.to_account)
    return seq
  }, [hops])

  const graphNodes = useMemo(() => {
    if (!hops.length) return []
    const ids = new Set(path)
    const nodes = [...ids].map((id) => {
      const hop = hops.find(
        (h) => h.from_account === id || h.to_account === id
      )
      return {
        id,
        label: id,
        risk_score: 80,
        risk_category: 'high',
        degree: 3,
      }
    })
    return nodes
  }, [hops, path])

  const graphEdges = useMemo(() => hops.map((h) => ({
    source: h.from_account,
    target: h.to_account,
    weight: h.amount,
    count: 1,
    suspicious: true,
  })), [hops])

  const riskByAccount = useMemo(() => {
    const map = {}
    ;(result?.accounts || []).forEach((a) => { map[a] = 'high' })
    return map
  }, [result])

  return (
    <div className="page">
      <Header
        title="Money Trail"
        subtitle="Reconstruct chronological money movement — WHO, WHEN, HOW MUCH, FROM, TO"
      />

      <div className="card card-pad mb-2">
        <div className="row" style={{ alignItems: 'flex-end' }}>
          <div className="field" style={{ flex: 1, marginBottom: 0 }}>
            <label>Source account</label>
            <input
              className="input mono"
              placeholder="e.g. AC9001 or AC381"
              value={source}
              onChange={(e) => setSource(e.target.value)}
            />
          </div>
          <div className="field" style={{ flex: 1, marginBottom: 0 }}>
            <label>Destination (optional)</label>
            <input
              className="input mono"
              placeholder="e.g. CO-03 — leave empty to follow the money"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
            />
          </div>
          <div className="field" style={{ width: 160, marginBottom: 0 }}>
            <label>Max minutes</label>
            <select
              className="select"
              value={maxMinutes}
              onChange={(e) => setMaxMinutes(e.target.value)}
            >
              <option value={15}>15 min</option>
              <option value={30}>30 min</option>
              <option value={60}>60 min</option>
              <option value={1440}>24 hours</option>
            </select>
          </div>
          <button
            className="btn btn-primary"
            onClick={trace}
            disabled={loading}
          >
            {loading ? <span className="spin" /> : '⇢ Trace Money'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {result && !result.error && result.hops > 0 && (
        <>
          {/* trail summary */}
          <div className="alert-banner success mb-2">
            <span>✓</span>
            <div style={{ flex: 1 }}>
              <strong>{result.summary}</strong>
            </div>
          </div>
          
          {/* Tracing Disclaimer */}
          {result.tracing_disclaimer && (
            <div className="alert-banner info mb-2">
              <span>⚠</span>
              <div className="small">
                <strong>Important:</strong> {result.tracing_disclaimer}
              </div>
            </div>
          )}

          <div className="grid grid-6 mb-2">
            <SummaryCard label="Trail ID" value={result.trail_id || '—'} />
            <SummaryCard label="Starting amount"
              value={formatINR(result.starting_amount)} />
            <SummaryCard label="Tracked amount"
              value={formatINR(result.tracked_amount)} />
            <SummaryCard label="Hops" value={result.hops} />
            <SummaryCard label="Duration"
              value={`${result.duration_minutes} min`} />
            <SummaryCard label="Accounts"
              value={result.accounts_involved} />
          </div>

          <div className="card card-pad mb-2">
            <div className="tabs">
              {[
                ['timeline', 'Timeline'],
                ['graph', 'Graph'],
                ['table', 'Table'],
                ['evidence', 'Evidence'],
              ].map(([key, label]) => (
                <button
                  key={key}
                  className={`tab ${tab === key ? 'active' : ''}`}
                  onClick={() => setTab(key)}
                >
                  {label}
                </button>
              ))}
            </div>

            {tab === 'timeline' && (
              <Timeline
                items={hops.map((h) => ({
                  timestamp: h.timestamp,
                  sender_account: h.from_account,
                  receiver_account: h.to_account,
                  amount: h.amount,
                  transaction_type: 'transfer',
                  suspicious: true,
                  note: `TX ${h.transaction_id}`,
                }))}
              />
            )}

            {tab === 'graph' && (
              <NetworkGraph
                nodes={graphNodes}
                edges={graphEdges}
                highlightPath={path}
                height={420}
                onNodeClick={(id) => navigate(`/account/${id}`)}
              />
            )}

            {tab === 'table' && (
              <DataTable
                columns={[
                  { key: 'hop_index', label: 'Hop' },
                  { key: 'timestamp', label: 'When',
                    render: (v) => formatDateTime(v) },
                  { key: 'from_account', label: 'From' },
                  { key: 'to_account', label: 'To' },
                  { key: 'amount', label: 'Amount', className: 'num',
                    render: (v) => formatINR(v) },
                  { key: 'transaction_id', label: 'Transaction' },
                ]}
                rows={hops.map((h) => ({ ...h, id: h.hop_index }))}
              />
            )}

            {tab === 'evidence' && (
              <EvidenceView hops={hops} formatINR={formatINR} formatDateTime={formatDateTime} />
            )}
          </div>

          {result.cashout_intelligence?.available && (
            <div className="card card-pad mb-2">
              <div className="card-title">
                Cash-out Intelligence — Extension
              </div>
              <div className="grid grid-3">
                <Feature label="Likely cash-out location"
                  value={result.cashout_intelligence.likely_cashout_location} />
                <Feature label="Supporting transactions"
                  value={result.cashout_intelligence.supporting_transactions} />
                <Feature label="Confidence"
                  value={result.cashout_intelligence.confidence} />
              </div>
              <div className="disclaimer">
                {result.cashout_intelligence.disclaimer}
              </div>
            </div>
          )}
          {result.cashout_intelligence &&
            !result.cashout_intelligence.available && (
              <div className="alert-banner info">
                <span>ℹ</span>
                <span>
                  {result.cashout_intelligence.message}
                </span>
              </div>
            )}
        </>
      )}

      {result?.error && (
        <EmptyState
          icon="⇢"
          title="No trail found"
          desc={result.error}
        />
      )}

      {!result && (
        <div className="card card-pad">
          <div className="card-title">Recent Trails</div>
          {trails.length ? (
            <DataTable
              columns={[
                { key: 'trail_id', label: 'Trail' },
                { key: 'source_account', label: 'Source' },
                { key: 'terminal_account', label: 'Terminal' },
                { key: 'hops', label: 'Hops', className: 'num' },
                { key: 'duration_minutes', label: 'Duration', className: 'num',
                  render: (v) => `${v} min` },
                { key: 'starting_amount', label: 'Starting', className: 'num',
                  render: (v) => formatINR(v) },
                { key: 'summary', label: 'Summary',
                  render: (v) => (
                    <span className="small">{v}</span>
                  ),
                },
              ]}
              rows={trails.map((t) => ({ ...t, id: t.trail_id }))}
              onRowClick={(row) => {
                api(`/api/trails/${row.trail_id}`)
                  .then(setResult)
                  .catch((e) => setError(e.message))
              }}
              emptyMessage="No trails generated yet."
            />
          ) : (
            <EmptyState
              icon="⇢"
              title="No trails yet"
              desc="Trace money from a source account to reconstruct its movement."
            />
          )}
        </div>
      )}
    </div>
  )
}

function EvidenceView({ hops, formatINR, formatDateTime }) {
  return (
    <div className="card card-pad">
      <div className="card-title">Supporting Transaction Evidence</div>
      <div className="small muted mb-2">
        Each hop below corresponds to an actual transaction record. 
        Click a transaction ID to view full details.
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Hop</th>
              <th>When</th>
              <th>From</th>
              <th>To</th>
              <th className="num">Amount</th>
              <th>Transaction ID</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {hops.map((h) => (
              <tr key={h.hop_index}>
                <td>{h.hop_index}</td>
                <td>{formatDateTime(h.timestamp)}</td>
                <td className="mono">{h.from_account}</td>
                <td className="mono">{h.to_account}</td>
                <td className="num">{formatINR(h.amount)}</td>
                <td className="mono">{h.transaction_id}</td>
                <td>
                  <button
                    className="btn btn-sm btn-ghost"
                    onClick={() => window.open(`/transactions/${h.transaction_id}`, '_blank')}
                    title="View transaction details"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="disclaimer mt-2">
        <strong>Evidence Note:</strong> Each row above represents an actual transaction record 
        from the imported dataset. The trail shows a temporally connected sequence of 
        transactions — it does not prove that the same currency units flowed through every 
        account. Branching (multiple outgoing transfers from one hop) means only a portion 
        of the received value may follow the shown path.
      </div>
    </div>
  )
}

function SummaryCard({ label, value }) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value" style={{ fontSize: 18 }}>
        {value}
      </div>
    </div>
  )
}

function Feature({ label, value }) {
  return (
    <div>
      <div className="small muted">{label}</div>
      <div style={{ fontWeight: 600 }}>{value}</div>
    </div>
  )
}

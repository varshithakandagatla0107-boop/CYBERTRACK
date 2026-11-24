import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import RiskBadge from '../components/RiskBadge'
import RiskBreakdown from '../components/RiskBreakdown'
import NetworkGraph from '../components/NetworkGraph'
import Timeline from '../components/Timeline'
import DataTable from '../components/DataTable'
import { EmptyState, LoadingState, ErrorState } from '../components/States'
import { formatINR, formatDateTime } from '../api/client'

export default function AccountDetail() {
  const { accountId } = useParams()
  const { api } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [ego, setEgo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [reason, setReason] = useState('')
  const [trailLoading, setTrailLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [detail, graph] = await Promise.all([
        api(`/api/accounts/${accountId}`),
        api(`/api/network/${accountId}`),
      ])
      setData(detail)
      setEgo(graph)
      setStatus(detail.status)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api, accountId])

  useEffect(() => { load() }, [load])

  const updateStatus = async (newStatus) => {
    try {
      await api(
        `/api/accounts/${accountId}/status?status=${newStatus}` +
        (reason ? `&reason=${encodeURIComponent(reason)}` : ''),
        { method: 'PATCH' }
      )
      const detail = await api(`/api/accounts/${accountId}`)
      setData(detail)
      setStatus(detail.status)
    } catch (err) {
      setError(err.message)
    }
  }

  const traceMoney = async () => {
    setTrailLoading(true)
    try {
      const result = await api('/api/trails/trace', {
        method: 'POST',
        body: JSON.stringify({
          source: accountId,
        }),
      })
      navigate('/money-trail', { state: { trail: result } })
    } catch (err) {
      setError(err.message)
      setTrailLoading(false)
    }
  }

  const createInvestigation = async () => {
    try {
      const inv = await api('/api/investigations', {
        method: 'POST',
        body: JSON.stringify({
          title: `Suspicious activity — ${accountId}`,
          priority: data?.risk?.category === 'high'
            ? 'high' : 'medium',
          accounts: [accountId],
          notes: `Auto-attached from account investigation of ${accountId}.`,
        }),
      })
      navigate(`/investigations/${inv.investigation_id}`)
    } catch (err) {
      setError(err.message)
    }
  }

  if (loading && !data) {
    return (
      <div className="page">
        <LoadingState label={`Loading account ${accountId}…`} />
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="page">
        <ErrorState message={error} onRetry={load} />
      </div>
    )
  }

  if (!data) return null

  const r = data.risk
  const f = data.features || {}
  const priority = r.category === 'high'
    ? 'HIGH' : r.category === 'medium' ? 'MEDIUM' : 'LOW'

  return (
    <div className="page">
      <Header
        title={`Account ${accountId}`}
        subtitle="Account investigation"
      >
        <div className="row" style={{ gap: 8 }}>
          <button className="btn" onClick={() => navigate('/network')}>
            ◎ Network Explorer
          </button>
          <button
            className="btn btn-primary"
            onClick={traceMoney}
            disabled={trailLoading}
            title="Trace money from this account downstream"
          >
            {trailLoading ? <span className="spin" /> : '⇢ Trace Money'}
          </button>
          <button
            className="btn btn-primary"
            onClick={createInvestigation}
            title="Open a new investigation with this account attached"
          >
            + Create Investigation
          </button>
        </div>
      </Header>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* summary strip */}
      <div className="card card-pad mb-2">
        <div className="row-between">
          <div className="row" style={{ gap: 20 }}>
            <div>
              <div className="small muted">ACCOUNT</div>
              <div className="mono" style={{ fontSize: 18, fontWeight: 700 }}>
                {accountId}
              </div>
            </div>
            <div>
              <div className="small muted">RISK</div>
              <div style={{ marginTop: 2 }}>
                <RiskBadge score={r.score} category={r.category} />
              </div>
            </div>
            <div>
              <div className="small muted">PRIORITY</div>
              <div style={{ fontWeight: 700, marginTop: 2 }}>
                {priority}
              </div>
            </div>
            <div>
              <div className="small muted">STATUS</div>
              <div style={{ marginTop: 2 }}>
                <span className="badge badge-blue">
                  {status || 'unreviewed'}
                </span>
              </div>
            </div>
          </div>
          <div className="row" style={{ gap: 28 }}>
            <div className="small">
              <div className="muted">Received</div>
              <strong>{formatINR(f.in_amount)}</strong>
            </div>
            <div className="small">
              <div className="muted">Sent</div>
              <strong>{formatINR(f.out_amount)}</strong>
            </div>
            <div className="small">
              <div className="muted">Transactions</div>
              <strong>{f.tx_count}</strong>
            </div>
            <div className="small">
              <div className="muted">Counterparties</div>
              <strong>{f.counterparties}</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-main">
        <div>
          {/* why suspicious */}
          <div className="card card-pad mb-2">
            <div className="card-title">
              Why is this account suspicious?
            </div>
            <ul className="reason-list">
              {(data.reasons || []).map((reasonText, i) => (
                <li key={i}>{reasonText}</li>
              ))}
            </ul>
            <div className="divider" />
            <div className="card-title">Why this score?</div>
            <RiskBreakdown
              contributors={
                Array.isArray(r.contributors)
                  ? r.contributors
                  : Object.entries(r.contributors || {})
              }
              total={r.score}
            />
            <div className="disclaimer">
              Prototype analytical scoring model. Risk score is
              an analytical prioritisation signal, not a
              determination of fraud. Detection method:{' '}
              {r.detection_method}.
            </div>
          </div>

          {/* behavioural features */}
          <div className="card card-pad mb-2">
            <div className="card-title">Behavioural Features</div>
            <div className="grid grid-4">
              <Feature label="Transaction velocity"
                value={`${Number(f.velocity || 0).toFixed(1)} tx/hr (peak)`} />
              <Feature label="Rapid pass-through"
                value={`${Number(f.rapid_pass_pct || 0).toFixed(0)}% within 15 min`} />
              <Feature label="In/Out ratio"
                value={Number(f.in_out_ratio || 0).toFixed(2)} />
              <Feature label="Transaction burst"
                value={`${(Number(f.burst_score || 0) * 100).toFixed(0)}%`} />
              <Feature label="Network degree"
                value={f.degree ?? '—'} />
              <Feature label="Temporal concentration"
                value={`${(Number(f.temporal_concentration || 0) * 100).toFixed(0)}%`} />
              <Feature label="In-degree"
                value={f.in_degree ?? '—'} />
              <Feature label="Out-degree"
                value={f.out_degree ?? '—'} />
            </div>
          </div>

          {/* timeline */}
          <div className="card card-pad">
            <div className="card-title">Timeline</div>
            <Timeline
              items={(data.transactions || []).slice(0, 25).map((t) => ({
                ...t,
                suspicious: r.category === 'high',
              }))}
            />
          </div>
        </div>

        <div>
          {/* network position */}
          <div className="card card-pad mb-2">
            <div className="card-title">Network Position</div>
            {ego ? (
              <NetworkGraph
                nodes={ego.nodes}
                edges={ego.edges}
                selectedId={accountId}
                height={360}
                onNodeClick={(id) => navigate(`/account/${id}`)}
              />
            ) : (
              <EmptyState
                icon="◎"
                title="No network data"
                desc="This account has no visible connections."
              />
            )}
            {ego?.suspicious_neighbours?.length > 0 && (
              <div className="mt-1 small">
                <span className="muted">Suspicious neighbours: </span>
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
          </div>

          {/* classification (human-in-the-loop) */}
          <div className="card card-pad">
            <div className="card-title">
              Investigator Classification
            </div>
            <div className="small muted mb-1">
              The system suggests — the investigator decides.
            </div>
            <div className="field">
              <label>Mark account as</label>
              <select
                className="select"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="unreviewed">Unreviewed</option>
                <option value="needs_review">Needs Review</option>
                <option value="confirmed_suspicious">
                  Confirmed Suspicious
                </option>
                <option value="false_positive">False Positive</option>
                <option value="legitimate">Legitimate</option>
              </select>
            </div>
            {status === 'false_positive' && (
              <div className="field">
                <label>
                  Reason (required for false positive)
                </label>
                <textarea
                  className="input"
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Why is this a false positive?"
                />
              </div>
            )}
            <button
              className="btn btn-primary"
              style={{ width: '100%' }}
              onClick={() => updateStatus(status)}
              disabled={status === 'false_positive' && !reason.trim()}
            >
              Save classification
            </button>
            {data.analyst_note && (
              <div className="disclaimer">
                Note: {data.analyst_note}
              </div>
            )}
          </div>

          {/* Next Steps - Contextual actions for investigator */}
          <div className="card card-pad mb-2">
            <div className="card-title">Next Steps</div>
            <div className="grid grid-2">
              <button
                className="btn"
                onClick={traceMoney}
                disabled={trailLoading}
                title="Trace money downstream from this account"
              >
                ⇢ Trace Money Trail
              </button>
              <button
                className="btn"
                onClick={() => navigate(`/network/${accountId}`)}
                title="Explore network connections around this account"
              >
                ◎ Explore Network
              </button>
              <button
                className="btn"
                onClick={() => navigate('/money-trail', { state: { source: accountId } })}
                title="Open Money Trail with this account as source"
              >
                ⇢ Open Money Trail
              </button>
              <button
                className="btn"
                onClick={createInvestigation}
                title="Create investigation with this account attached"
              >
                + Create Investigation
              </button>
            </div>
          </div>

          {/* Data Provenance */}
          <div className="card card-pad">
            <div className="card-title">Data Provenance</div>
            <div className="small muted">
              <div>Risk analysis method: {r.detection_method}</div>
              <div>Dataset: {data.dataset?.name || 'Unknown'}</div>
              <div>Analysis timestamp: {data.dataset?.created_at || 'Unknown'}</div>
              <div className="mt-1 disclaimer">
                Risk scores support investigative prioritization. 
                They do not establish fraud or guilt. 
                Behavioural features calculated from imported transaction data.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Feature({ label, value }) {
  return (
    <div style={{
      padding: '10px 12px',
      border: '1px solid var(--line)',
      borderRadius: 'var(--radius)',
    }}>
      <div className="small muted">{label}</div>
      <div style={{ fontWeight: 600, marginTop: 2 }}>{value}</div>
    </div>
  )
}

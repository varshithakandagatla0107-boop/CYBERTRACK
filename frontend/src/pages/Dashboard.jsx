import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import MetricCard from '../components/MetricCard'
import RiskBadge from '../components/RiskBadge'
import DataTable from '../components/DataTable'
import NetworkGraph from '../components/NetworkGraph'
import { EmptyState, LoadingState, ErrorState } from '../components/States'
import { formatINR, formatDateTime } from '../api/client'

export default function Dashboard() {
  const { api } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [revealed, setRevealed] = useState(false)
  const [graphData, setGraphData] = useState(null)
  const [loadingGraph, setLoadingGraph] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const d = await api('/api/dashboard')
      setData(d)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api])

  useEffect(() => { load() }, [load])

  const loadDemo = async () => {
    setLoading(true)
    try {
      await api('/api/data/demo', { method: 'POST' })
      await load()
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const revealNetwork = async () => {
    setRevealed(true)
    setLoadingGraph(true)
    try {
      const g = await api(
        '/api/network?high_risk_only=true&limit=120'
      )
      setGraphData(g)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingGraph(false)
    }
  }

  if (loading && !data) {
    return (
      <div className="page">
        <LoadingState label="Loading dashboard…" />
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

  if (!data?.loaded) {
    return (
      <div className="page">
        <Header title="Dashboard" />
        <EmptyState
          icon="▦"
          title="No transactions loaded"
          desc="No transactions loaded. Upload a dataset or use the demonstration dataset."
          action={
            <button
              className="btn btn-primary"
              onClick={loadDemo}
            >
              Load Demonstration Case
            </button>
          }
        />
      </div>
    )
  }

  const m = data.metrics

  return (
    <div className="page">
      <Header
        title="Dashboard"
        subtitle={`${data.dataset?.name} · analysed ${data.dataset?.created_at}`}
      >
        <div className="row" style={{ gap: 8 }}>
          <button className="btn" onClick={loadDemo}>↻ Load Demonstration Case</button>
          {data.risk_disclaimer && (
            <button className="btn btn-sm btn-ghost"
              onClick={() => navigate('/priority')}>
              Risk Disclaimer
            </button>
          )}
        </div>
      </Header>

      {!revealed && (
        <div className="alert-banner info">
          <span>◉</span>
          <div style={{ flex: 1 }}>
            <strong>
              {m.total_transactions.toLocaleString()} transactions
              reviewed. {m.suspicious_accounts} high-priority
              accounts identified.
            </strong>
            <div className="small" style={{ marginTop: 2 }}>
              Individually these transactions look ordinary.
              Once connected, CyberTrack reveals the hidden
              money trail.
            </div>
          </div>
          <button className="btn btn-primary" onClick={revealNetwork}>
            Reveal Hidden Network
          </button>
        </div>
      )}

      {revealed && !loadingGraph && (
        <div className="alert-banner success">
          <span>✓</span>
          <div>
            <strong>Hidden network revealed.</strong>{' '}
            Red nodes and edges form part of the same
            high-risk money trail.{' '}
            <button className="btn btn-sm btn-ghost"
              onClick={() => navigate('/network')}>
              Open Network Explorer →
            </button>
          </div>
        </div>
      )}

      {data.risk_disclaimer && (
        <div className="disclaimer" style={{ marginBottom: 16 }}>
          {data.risk_disclaimer}
        </div>
      )}

      <div className="grid grid-6 mb-2">
        <MetricCard
          label="Total Transactions"
          value={m.total_transactions.toLocaleString()}
        />
        <MetricCard
          label="Total Value"
          value={formatINR(m.total_value)}
        />
        <MetricCard
          label="Accounts Analyzed"
          value={m.accounts_analyzed.toLocaleString()}
        />
        <MetricCard
          label="Suspicious Accounts"
          value={m.suspicious_accounts}
          tone={m.suspicious_accounts > 0 ? 'alert' : ''}
        />
        <MetricCard
          label="High-Risk Networks"
          value={m.high_risk_networks}
          tone={m.high_risk_networks > 0 ? 'warn' : ''}
        />
        <MetricCard
          label="Active Investigations"
          value={m.active_investigations}
        />
      </div>

      <div className="grid-main">
        <div>
          {/* risk overview */}
          <div className="card card-pad mb-2">
            <div className="card-title">Risk Overview</div>
            <div className="row" style={{ gap: 24 }}>
              <div>
                <RiskBadge
                  score={70}
                  category="high"
                  short
                />
                <div className="mt-1" style={{ fontSize: 22, fontWeight: 700 }}>
                  {data.risk_overview.high}
                </div>
                <div className="small muted">High Risk</div>
              </div>
              <div>
                <RiskBadge
                  score={55}
                  category="medium"
                  short
                />
                <div className="mt-1" style={{ fontSize: 22, fontWeight: 700 }}>
                  {data.risk_overview.medium}
                </div>
                <div className="small muted">Medium Risk</div>
              </div>
              <div>
                <RiskBadge
                  score={10}
                  category="low"
                  short
                />
                <div className="mt-1" style={{ fontSize: 22, fontWeight: 700 }}>
                  {data.risk_overview.low}
                </div>
                <div className="small muted">Low Risk</div>
              </div>
              <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                <div className="small muted">Detection method</div>
                <div className="small" style={{ fontWeight: 600 }}>
                  {data.detection_method}
                </div>
              </div>
            </div>
          </div>

          {/* top priority accounts */}
          <div className="card card-pad mb-2">
            <div className="row-between mb-1">
              <div className="card-title" style={{ margin: 0 }}>
                Top Priority Accounts
              </div>
              <button
                className="btn btn-sm btn-ghost"
                onClick={() => navigate('/priority')}
              >
                View all →
              </button>
            </div>
            <DataTable
              columns={[
                { key: 'rank', label: 'Rank' },
                {
                  key: 'account_id', label: 'Account',
                  render: (v) => (
                    <span className="mono">{v}</span>
                  ),
                },
                {
                  key: 'risk_score', label: 'Risk',
                  render: (v, r) => (
                    <RiskBadge score={v} category={r.risk_category} short />
                  ),
                },
                { key: 'volume', label: 'Volume', className: 'num',
                  render: (v) => formatINR(v) },
              ]}
              rows={(data.top_accounts || []).slice(0, 6).map((a, i) => ({
                ...a, rank: i + 1, id: a.account_id,
              }))}
              onRowClick={(row) =>
                navigate(`/account/${row.account_id}`)
              }
            />
          </div>

          {/* recent suspicious activity */}
          <div className="card card-pad">
            <div className="card-title">Recent Suspicious Activity</div>
            <DataTable
              columns={[
                {
                  key: 'timestamp', label: 'Time',
                  render: (v) => formatDateTime(v),
                },
                { key: 'sender_account', label: 'From' },
                { key: 'receiver_account', label: 'To' },
                {
                  key: 'amount', label: 'Amount', className: 'num',
                  render: (v) => formatINR(v),
                },
                { key: 'transaction_type', label: 'Type' },
              ]}
              rows={(data.recent_suspicious || []).map((t, i) => ({
                ...t, id: i,
              }))}
              onRowClick={(row) =>
                navigate(`/account/${row.sender_account}`)
              }
              emptyMessage="No suspicious activity recorded."
            />
          </div>
        </div>

        {/* network snapshot */}
        <div>
          <div className="card card-pad mb-2">
            <div className="card-title">Network Snapshot</div>
            {revealed && graphData ? (
              loadingGraph ? (
                <LoadingState label="Revealing hidden network…" />
              ) : (
                <NetworkGraph
                  nodes={graphData.nodes}
                  edges={graphData.edges}
                  height={380}
                  onNodeClick={(id) =>
                    navigate(`/account/${id}`)
                  }
                />
              )
            ) : (
              <EmptyState
                icon="◎"
                title="Network hidden"
                desc="Click “Reveal Hidden Network” to connect the transactions."
                action={
                  <button
                    className="btn btn-primary"
                    onClick={revealNetwork}
                  >
                    Reveal Hidden Network
                  </button>
                }
              />
            )}
          </div>
          {data.alerts?.length > 0 && (
            <div className="card card-pad">
              <div className="card-title">Latest Alerts</div>
              {data.alerts.slice(0, 4).map((a) => (
                <div
                  key={a.id}
                  style={{
                    padding: '8px 0',
                    borderBottom: '1px solid #eef2f6',
                  }}
                >
                  <div className="row-between">
                    <span style={{ fontWeight: 600, fontSize: 12.5 }}>
                      {a.title}
                    </span>
                    <span className={`badge badge-${a.severity}`}>
                      {a.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className="small muted mt-1">
                    {a.description.slice(0, 90)}…
                  </div>
                </div>
              ))}
              <button
                className="btn btn-sm btn-ghost mt-1"
                onClick={() => navigate('/alerts')}
              >
                View all alerts →
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="disclaimer">
        All transactions shown in this prototype are synthetic
        demonstration data. Risk scores are analytical
        prioritisation signals, not determinations of fraud.
      </div>
    </div>
  )
}

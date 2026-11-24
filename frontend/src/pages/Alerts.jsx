import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import DataTable from '../components/DataTable'
import { EmptyState, LoadingState, ErrorState } from '../components/States'
import { formatINR, formatDateTime } from '../api/client'

const TYPE_LABELS = {
  rapid_pass_through: 'Rapid Pass-Through',
  high_connectivity: 'High Connectivity',
  transaction_burst: 'Transaction Burst',
  suspicious_divergence: 'Structuring / Splitting',
  rapid_multi_hop: 'Rapid Multi-Hop',
  suspicious_convergence: 'Suspicious Convergence',
}

export default function Alerts() {
  const { api } = useAuth()
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [severity, setSeverity] = useState('')
  const [alertType, setAlertType] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const q = new URLSearchParams()
    if (severity) q.set('severity', severity)
    if (alertType) q.set('alert_type', alertType)
    try {
      const d = await api(`/api/alerts?${q}`)
      setAlerts(d.alerts || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api, severity, alertType])

  useEffect(() => { load() }, [load])

  const updateStatus = async (id, status) => {
    try {
      await api(`/api/alerts/${id}/status?status=${status}`, {
        method: 'PATCH',
      })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="page">
      <Header
        title="Alerts"
        subtitle={`${alerts.length} pattern alerts`}
      >
        <select
          className="select"
          style={{ width: 140 }}
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
        >
          <option value="">All severities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
        </select>
        <select
          className="select"
          style={{ width: 200 }}
          value={alertType}
          onChange={(e) => setAlertType(e.target.value)}
        >
          <option value="">All patterns</option>
          {Object.entries(TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </Header>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState label="Loading alerts…" />
      ) : alerts.length === 0 ? (
        <EmptyState
          icon="⚠"
          title="No alerts"
          desc="No pattern alerts match the current filters."
        />
      ) : (
        <div className="grid" style={{ gridTemplateColumns: '1fr' }}>
          {alerts.map((a) => (
            <div key={a.id} className="card card-pad">
              <div className="row-between">
                <div className="row">
                  <span className={`badge badge-${a.severity}`}>
                    {a.severity.toUpperCase()}
                  </span>
                  <strong>{TYPE_LABELS[a.alert_type] || a.alert_type}</strong>
                </div>
                <span className="small muted">
                  {a.risk_score ? `Risk ${a.risk_score}` : ''}
                </span>
              </div>
              <div className="mt-1" style={{ fontWeight: 600 }}>
                {a.title}
              </div>
              <div className="small mt-1" style={{ maxWidth: 900 }}>
                {a.description}
              </div>
              <div className="row mt-2 small" style={{
                flexWrap: 'wrap', gap: 18,
              }}>
                {a.occurred_at && (
                  <span>
                    <span className="muted">When: </span>
                    {formatDateTime(a.occurred_at)}
                  </span>
                )}
                {a.amount && (
                  <span>
                    <span className="muted">Amount: </span>
                    {formatINR(a.amount)}
                  </span>
                )}
                <span>
                  <span className="muted">Accounts: </span>
                  {a.account_list?.map((ac) => (
                    <button
                      key={ac}
                      className="btn btn-sm btn-ghost"
                      onClick={() => navigate(`/account/${ac}`)}
                    >
                      {ac}
                    </button>
                  ))}
                </span>
              </div>
              <div className="row-between mt-2">
                <div className="small muted">
                  <span className="muted">Recommended: </span>
                  {a.recommended_action}
                </div>
                <div className="row" style={{ gap: 4 }}>
                  {['acknowledged', 'escalated', 'closed'].map(
                    (s) => (
                      <button
                        key={s}
                        className={`btn btn-sm ${a.status === s ? 'btn-primary' : ''}`}
                        onClick={() => updateStatus(a.id, s)}
                      >
                        {s}
                      </button>
                    )
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

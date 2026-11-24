import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import { LoadingState, ErrorState } from '../components/States'

export default function Analytics() {
  const { api } = useAuth()
  const [model, setModel] = useState(null)
  const [dist, setDist] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api('/api/analytics/model'),
      api('/api/analytics/risk-distribution'),
    ])
      .then(([m, d]) => {
        setModel(m)
        setDist(d.distribution || [])
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [api])

  if (loading) {
    return (
      <div className="page">
        <LoadingState label="Loading analytics…" />
      </div>
    )
  }
  if (error && !model) {
    return (
      <div className="page">
        <ErrorState message={error} />
      </div>
    )
  }

  const chartData = [
    { name: 'Low (0–39)', count: dist.find(
        (d) => d.bucket.includes('Low'))?.n || 0 },
    { name: 'Medium (40–69)', count: dist.find(
        (d) => d.bucket.includes('Medium'))?.n || 0 },
    { name: 'High (70–100)', count: dist.find(
        (d) => d.bucket.includes('High'))?.n || 0 },
  ]

  return (
    <div className="page">
      <Header
        title="Analytics & Model Transparency"
        subtitle="What the detection layer does, and what it does not"
      />

      <div className="alert-banner info">
        <span>ℹ</span>
        <div>
          <strong>Detection method: {model.detection_method}.</strong>
          {model.isolation_forest_available
            ? ' Scikit-learn Isolation Forest is active.'
            : ' Scikit-learn is unavailable — the deterministic analytical fallback is active.'}
        </div>
      </div>

      <div className="grid-main">
        <div>
          <div className="card card-pad mb-2">
            <div className="card-title">
              Risk distribution across {model.accounts_analyzed}{' '}
              accounts
            </div>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]}>
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="grid grid-3 mt-2">
              <div className="small">
                <div className="muted">Accounts analyzed</div>
                <strong>{model.accounts_analyzed}</strong>
              </div>
              <div className="small">
                <div className="muted">Anomaly signals</div>
                <strong>{model.anomalies_detected}</strong>
              </div>
              <div className="small">
                <div className="muted">Last analysis</div>
                <strong>{model.last_analysis || '—'}</strong>
              </div>
            </div>
          </div>

          <div className="card card-pad">
            <div className="card-title">
              Features used by the model
            </div>
            <div className="grid grid-3">
              {model.features_used.map((f) => (
                <div
                  key={f}
                  style={{
                    padding: '8px 12px',
                    border: '1px solid var(--line)',
                    borderRadius: 'var(--radius)',
                    fontSize: 13,
                  }}
                >
                  {f}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div className="card card-pad mb-2">
            <div className="card-title">Scoring model</div>
            <div className="small">
              <div className="muted">Risk thresholds</div>
              <div className="mt-1">
                <span className="badge badge-high">HIGH ≥ 70</span>{' '}
                <span className="badge badge-medium">MED ≥ 40</span>{' '}
                <span className="badge badge-low">LOW &lt; 40</span>
              </div>
            </div>
            <div className="divider" />
            <div className="small muted mb-1">
              Signal weights (configurable)
            </div>
            {Object.entries(model.weights || {}).map(
              ([k, v]) => (
                <div key={k} className="contributor-row">
                  <span className="contributor-name">{k}</span>
                  <span className="contributor-bar">
                    <span
                      className="contributor-fill"
                      style={{
                        width: `${(v / 22) * 100}%`,
                      }}
                    />
                  </span>
                  <span className="contributor-val">{v}</span>
                </div>
              )
            )}
          </div>

          <div className="card card-pad">
            <div className="card-title">Model disclaimer</div>
            <div className="disclaimer" style={{ marginTop: 0 }}>
              {model.risk_disclaimer}
            </div>
            <div className="mt-2 small">
              CyberTrack does not declare fraud. It ranks
              and explains so a human investigator can
              decide where to look first.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

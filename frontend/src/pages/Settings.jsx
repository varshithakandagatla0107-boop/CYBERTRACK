import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import { LoadingState, ErrorState } from '../components/States'

export default function Settings() {
  const { api, user } = useAuth()
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/api/settings')
      .then(setSettings)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [api])

  if (loading) {
    return (
      <div className="page">
        <LoadingState label="Loading settings…" />
      </div>
    )
  }
  if (error && !settings) {
    return (
      <div className="page">
        <ErrorState message={error} />
      </div>
    )
  }

  return (
    <div className="page">
      <Header
        title="Settings"
        subtitle={settings?.environment}
      />

      <div className="grid-main">
        <div>
          <div className="card card-pad mb-2">
            <div className="card-title">
              Analysis Parameters
            </div>
            <div className="grid grid-3">
              <Setting
                label="Rapid pass-through window"
                value={`${settings.analysis_parameters.rapid_pass_through_minutes} min`}
              />
              <Setting
                label="Burst detection window"
                value={`${settings.analysis_parameters.burst_window_minutes} min`}
              />
              <Setting
                label="Rapid multi-hop window"
                value={`${settings.analysis_parameters.rapid_multi_hop_minutes} min`}
              />
            </div>
            <div className="divider" />
            <div className="small muted mb-1">
              Risk signal weights
            </div>
            {Object.entries(
              settings.analysis_parameters.risk_weights || {}
            ).map(([k, v]) => (
              <div key={k} className="contributor-row">
                <span className="contributor-name">{k}</span>
                <span className="contributor-bar">
                  <span
                    className="contributor-fill"
                    style={{ width: `${(v / 22) * 100}%` }}
                  />
                </span>
                <span className="contributor-val">{v}</span>
              </div>
            ))}
          </div>

          <div className="card card-pad">
            <div className="card-title">
              Future Authorized Integrations
            </div>
            <p className="small muted">
              These integrations do not currently exist in the
              prototype. The adapter interfaces are designed
              so authorised services can be connected later.
            </p>
            {settings.future_integrations?.map((f) => (
              <div
                key={f.name}
                className="row-between"
                style={{
                  padding: '10px 0',
                  borderBottom: '1px solid #eef2f6',
                }}
              >
                <span style={{ fontWeight: 600 }}>{f.name}</span>
                <span className="badge badge-neutral">
                  {f.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="card card-pad mb-2">
            <div className="card-title">Security Posture</div>
            <ul className="reason-list">
              <li>Authenticated access (JWT sessions)</li>
              <li>Role-based permissions (investigator / analyst / admin)</li>
              <li>Masked account identifiers where appropriate</li>
              <li>Audit logging of investigator actions</li>
              <li>Synthetic dataset warning displayed</li>
              <li>Server-side input &amp; CSV validation</li>
              <li>Parameterised database operations</li>
            </ul>
          </div>

          <div className="card card-pad">
            <div className="card-title">Data Privacy</div>
            <div className="disclaimer" style={{ marginTop: 0 }}>
              {settings.data_privacy}
            </div>
            <div className="mt-2 small">
              Signed in as <strong>{user?.full_name}</strong>{' '}
              ({user?.role}).
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Setting({ label, value }) {
  return (
    <div>
      <div className="small muted">{label}</div>
      <div style={{ fontWeight: 600 }}>{value}</div>
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [investigatorId, setInvestigatorId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(investigatorId, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const fill = (id) => {
    setInvestigatorId(id)
    setPassword('cybertrack-demo')
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>CYBERTRACK</h1>
        <div className="login-sub">
          PS-35 · Tracing Money Through Mule Accounts
        </div>
        {error && (
          <div className="alert-banner error mb-2">
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="iid">Investigator ID</label>
            <input
              id="iid"
              className="input"
              autoComplete="username"
              value={investigatorId}
              onChange={(e) =>
                setInvestigatorId(e.target.value)
              }
              placeholder="e.g. investigator"
            />
          </div>
          <div className="field">
            <label htmlFor="pwd">Password</label>
            <input
              id="pwd"
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          <button
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center' }}
            disabled={loading}
          >
            {loading ? <span className="spin" /> : 'Sign in'}
          </button>
        </form>
        <div className="demo-hint">
          <strong>Prototype Environment — Synthetic Data.</strong>
          <br />
          Demo credentials —{' '}
          <code>investigator</code> / <code>cybertrack-demo</code>
          <div className="mt-1 row" style={{ gap: 6 }}>
            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={() => fill('investigator')}
            >Investigator</button>
            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={() => fill('analyst')}
            >Analyst</button>
            <button
              type="button"
              className="btn btn-sm btn-ghost"
              onClick={() => fill('admin')}
            >Admin</button>
          </div>
        </div>
        <div className="disclaimer" style={{ marginTop: 14 }}>
          CyberTrack is a hackathon prototype. Demonstration data
          is synthetic. Risk scores support investigation
          prioritisation and do not establish guilt or fraud.
        </div>
      </div>
    </div>
  )
}

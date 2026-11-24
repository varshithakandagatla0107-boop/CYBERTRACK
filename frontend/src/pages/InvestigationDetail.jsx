import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import RiskBadge from '../components/RiskBadge'
import { EmptyState, LoadingState, ErrorState } from '../components/States'
import { formatINR, formatDateTime } from '../api/client'

const STATUSES = ['open', 'under_review', 'escalated', 'resolved', 'closed']

export default function InvestigationDetail() {
  const { id } = useParams()
  const { api } = useAuth()
  const navigate = useNavigate()
  const [inv, setInv] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notes, setNotes] = useState('')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const d = await api(`/api/investigations/${id}`)
      setInv(d)
      setNotes(d.notes || '')
      setStatus(d.status)
      setPriority(d.priority)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const update = async (patch) => {
    try {
      await api(`/api/investigations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(patch),
      })
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const removeEntity = async (entityType, entityId) => {
    // entities are attached at creation; note-based
    // removal is recorded in the audit trail
    await update({
      notes: `${notes}\n[Removed ${entityType}: ${entityId}]`,
    })
  }

  if (loading && !inv) {
    return (
      <div className="page">
        <LoadingState label="Loading investigation…" />
      </div>
    )
  }
  if (error && !inv) {
    return (
      <div className="page">
        <ErrorState message={error} onRetry={load} />
      </div>
    )
  }
  if (!inv) return null

  const accounts = inv.entities?.filter(
    (e) => e.entity_type === 'account'
  ) || []
  const trails = inv.entities?.filter(
    (e) => e.entity_type === 'money_trail'
  ) || []
  const others = inv.entities?.filter(
    (e) => !['account', 'money_trail'].includes(e.entity_type)
  ) || []

  return (
    <div className="page">
      <Header
        title={`${inv.investigation_id} — ${inv.title}`}
        subtitle={`Created ${inv.created_at} by ${inv.created_by}`}
      >
        <button
          className="btn btn-primary"
          onClick={() =>
            window.print()
          }
        >
          ⎙ Print Summary
        </button>
      </Header>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      <div className="card card-pad mb-2">
        <div className="row-between" style={{ flexWrap: 'wrap' }}>
          <div className="row" style={{ gap: 20 }}>
            <div>
              <div className="small muted">PRIORITY</div>
              <span className={`badge ${
                priority === 'high' ? 'badge-high'
                : priority === 'medium' ? 'badge-medium'
                : 'badge-low'
              }`}>
                {priority.toUpperCase()}
              </span>
            </div>
            <div>
              <div className="small muted">STATUS</div>
              <select
                className="select"
                style={{ width: 150 }}
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace('_', ' ').toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <div className="small muted">ASSIGNED</div>
              <strong>{inv.assigned_to}</strong>
            </div>
          </div>
          <div className="row">
            <button
              className="btn btn-primary"
              onClick={() => update({ status, priority })}
            >
              Save changes
            </button>
          </div>
        </div>
      </div>

      <div className="grid-main">
        <div>
          {/* attached accounts */}
          <div className="card card-pad mb-2">
            <div className="card-title">
              Accounts ({accounts.length})
            </div>
            {accounts.length ? (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Account</th>
                      <th>Risk</th>
                      <th>Category</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {inv.account_context.map((a) => (
                      <tr key={a.account_id}>
                        <td className="mono">
                          <button
                            className="btn btn-sm btn-ghost"
                            onClick={() =>
                              navigate(`/account/${a.account_id}`)
                            }
                          >
                            {a.account_id}
                          </button>
                        </td>
                        <td>
                          <RiskBadge score={a.risk_score} short />
                        </td>
                        <td>
                          <span className={`badge badge-${a.risk_category}`}>
                            {a.risk_category.toUpperCase()}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-sm btn-ghost"
                            onClick={() =>
                              navigate('/money-trail', {
                                state: { source: a.account_id },
                              })
                            }
                          >
                            Trace
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                icon="▤"
                title="No accounts attached"
                desc="Attach accounts from the priority queue or account pages."
              />
            )}
          </div>

          {/* attached trails */}
          {trails.length > 0 && (
            <div className="card card-pad mb-2">
              <div className="card-title">
                Money Trails ({trails.length})
              </div>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Trail</th>
                      <th>Route</th>
                      <th>Hops</th>
                      <th>Duration</th>
                      <th>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trails.map((t) => {
                      const trail = inv.trail_details?.find?.(
                        (x) => x.trail_id === t.entity_id
                      )
                      return (
                        <tr key={t.entity_id}>
                          <td className="mono">{t.entity_id}</td>
                          <td>
                            {trail
                              ? `${trail.source_account} → ${trail.terminal_account}`
                              : '—'}
                          </td>
                          <td>{trail?.hops ?? '—'}</td>
                          <td>{trail ? `${trail.duration_minutes} min` : '—'}</td>
                          <td className="num">
                            {trail ? formatINR(trail.starting_amount) : '—'}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* notes */}
          <div className="card card-pad">
            <div className="card-title">Investigator Notes</div>
            <textarea
              className="input"
              rows={6}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Observations, next steps, evidence references…"
            />
            <button
              className="btn btn-primary mt-2"
              onClick={() => update({ notes })}
            >
              Save notes
            </button>
          </div>
        </div>

        <div>
          <div className="card card-pad mb-2">
            <div className="card-title">Other Entities</div>
            {others.length ? (
              <div>
                {others.map((e) => (
                  <div
                    key={`${e.entity_type}-${e.entity_id}`}
                    className="row-between"
                    style={{
                      padding: '8px 0',
                      borderBottom: '1px solid #eef2f6',
                    }}
                  >
                    <span className="small">
                      <span className="muted">
                        {e.entity_type}:{' '}
                      </span>
                      <span className="mono">{e.entity_id}</span>
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="small muted">
                No transactions, clusters or alerts attached.
              </div>
            )}
          </div>

          <div className="card card-pad">
            <div className="card-title">Actions</div>
            <div className="grid" style={{ gridTemplateColumns: '1fr' }}>
              <button
                className="btn"
                onClick={() => update({ status: 'escalated' })}
              >
                ⚑ Escalate
              </button>
              <button
                className="btn"
                onClick={() => update({ status: 'under_review' })}
              >
                ◔ Mark Under Review
              </button>
              <button
                className="btn"
                onClick={() => update({ status: 'resolved' })}
              >
                ✓ Mark Resolved
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="disclaimer">
        CyberTrack supports the investigation but does not
        autonomously declare guilt. The investigator remains
        responsible for all conclusions.
      </div>
    </div>
  )
}

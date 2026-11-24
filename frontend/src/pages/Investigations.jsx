import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import DataTable from '../components/DataTable'
import { EmptyState, LoadingState, ErrorState } from '../components/States'

export default function Investigations() {
  const { api } = useAuth()
  const navigate = useNavigate()
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const q = status ? `?status=${status}` : ''
    try {
      const d = await api(`/api/investigations${q}`)
      setList(d.investigations || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api, status])

  useEffect(() => { load() }, [load])

  return (
    <div className="page">
      <Header
        title="Investigations"
        subtitle="Human-in-the-loop investigation workspace"
      >
        <select
          className="select"
          style={{ width: 160 }}
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="under_review">Under Review</option>
          <option value="escalated">Escalated</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </Header>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState label="Loading investigations…" />
      ) : list.length === 0 ? (
        <EmptyState
          icon="▤"
          title="No investigations"
          desc="Create an investigation from a priority account, an account detail page, or the money trail."
          action={
            <button
              className="btn btn-primary"
              onClick={() => navigate('/priority')}
            >
              Open Priority Accounts
            </button>
          }
        />
      ) : (
        <div className="card">
          <DataTable
            columns={[
              { key: 'investigation_id', label: 'ID' },
              { key: 'title', label: 'Title' },
              {
                key: 'priority', label: 'Priority',
                render: (v) => (
                  <span className={`badge ${
                    v === 'high' ? 'badge-high'
                    : v === 'medium' ? 'badge-medium'
                    : 'badge-low'
                  }`}>
                    {v.toUpperCase()}
                  </span>
                ),
              },
              { key: 'assigned_to', label: 'Assigned To' },
              { key: 'status', label: 'Status',
                render: (v) => (
                  <span className="badge badge-blue">
                    {v.replace('_', ' ').toUpperCase()}
                  </span>
                ),
              },
              { key: 'created_at', label: 'Created' },
              {
                key: 'actions', label: '',
                render: (_, r) => (
                  <button
                    className="btn btn-sm"
                    onClick={() =>
                      navigate(
                        `/investigations/${r.investigation_id}`
                      )
                    }
                  >
                    Open →
                  </button>
                ),
              },
            ]}
            rows={list.map((i) => ({
              ...i, id: i.investigation_id,
            }))}
            emptyMessage="No investigations found."
          />
        </div>
      )}

      <div className="disclaimer">
        The system detects, ranks, explains and suggests.
        The investigator decides: review, escalate, close,
        or mark false positive.
      </div>
    </div>
  )
}

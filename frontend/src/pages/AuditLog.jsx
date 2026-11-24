import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import DataTable from '../components/DataTable'
import { EmptyState, LoadingState, ErrorState } from '../components/States'

export default function AuditLog() {
  const { api } = useAuth()
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [investigator, setInvestigator] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const q = new URLSearchParams({ limit: '200' })
    if (investigator) q.set('investigator_id', investigator)
    try {
      const d = await api(`/api/audit?${q}`)
      setEntries(d.entries || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api, investigator])

  useEffect(() => { load() }, [load])

  return (
    <div className="page">
      <Header
        title="Audit Log"
        subtitle="Investigator accountability — who did what, when"
      >
        <input
          className="input"
          style={{ width: 200 }}
          placeholder="Filter by investigator…"
          value={investigator}
          onChange={(e) => setInvestigator(e.target.value)}
        />
      </Header>

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <LoadingState label="Loading audit log…" />
      ) : (
        <div className="card">
          <DataTable
            columns={[
              { key: 'timestamp', label: 'Timestamp',
                render: (v) => v || '—' },
              { key: 'investigator_id', label: 'Investigator' },
              { key: 'action', label: 'Action' },
              { key: 'entity_type', label: 'Entity Type',
                render: (v) => v || '—' },
              { key: 'entity_id', label: 'Entity',
                render: (v) => v || '—' },
              { key: 'action_type', label: 'Action Type' },
              {
                key: 'result', label: 'Result',
                render: (v) => (
                  <span className={`badge ${
                    v === 'success' ? 'badge-low' : 'badge-high'
                  }`}>
                    {v.toUpperCase()}
                  </span>
                ),
              },
            ]}
            rows={entries.map((e, i) => ({ ...e, id: e.id || i }))}
            emptyMessage="No audit entries found."
          />
        </div>
      )}

      <div className="disclaimer">
        The audit log records investigator actions for
        accountability. It does not store passwords or
        unnecessary sensitive financial data.
      </div>
    </div>
  )
}

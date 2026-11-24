import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import { EmptyState, LoadingState } from '../components/States'

const PIPELINE_STEPS = [
  'DATA RECEIVED',
  'VALIDATION',
  'FEATURE EXTRACTION',
  'GRAPH CONSTRUCTION',
  'ANOMALY ANALYSIS',
  'INVESTIGATION PRIORITIES',
]

export default function DataManagement() {
  const { api } = useAuth()
  const [status, setStatus] = useState(null)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [pipeline, setPipeline] = useState(null)
  const fileRef = useRef(null)

  const loadStatus = useCallback(async () => {
    try {
      const s = await api('/api/data/status')
      setStatus(s)
    } catch (err) {
      setError(err.message)
    }
  }, [api])

  useEffect(() => { loadStatus() }, [loadStatus])

  const runPipeline = (result) => {
    setPipeline({ step: 0 })
    const steps = [
      { label: 'DATA RECEIVED',
        detail: `✓ ${result.validation?.total_rows ?? result.transactions} transactions received` },
      { label: 'VALIDATION',
        detail: `✓ ${result.validation?.valid_rows ?? result.transactions} valid`
          + (result.validation?.flagged_rows
            ? ` · ⚠ ${result.validation.flagged_rows} flagged`
            : '') },
      { label: 'FEATURE EXTRACTION',
        detail: `✓ Complete — ${result.accounts} accounts` },
      { label: 'GRAPH CONSTRUCTION',
        detail: `✓ ${result.accounts} accounts · ${result.edges} relationships` },
      { label: 'ANOMALY ANALYSIS',
        detail: `✓ Complete (${result.detection_method})` },
      { label: 'INVESTIGATION PRIORITIES',
        detail: `✓ Generated — ${result.high_risk_accounts} high risk` },
    ]
    let i = 0
    const tick = () => {
      if (i >= steps.length) {
        setTimeout(() => setPipeline({ done: true, steps }), 400)
        return
      }
      setPipeline({ step: i, steps })
      i += 1
      setTimeout(tick, 450)
    }
    tick()
  }

  const loadDemo = async () => {
    setUploading(true)
    setError('')
    setPipeline(null)
    try {
      const result = await api('/api/data/demo', {
        method: 'POST',
      })
      runPipeline(result)
      await loadStatus()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const upload = async () => {
    if (!file) return
    setUploading(true)
    setError('')
    setPipeline(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/data/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${
            JSON.parse(
              localStorage.getItem('cybertrack_session')
            )?.token || ''
          }`,
        },
        body: form,
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(
          data.detail || `Upload failed (${res.status})`
        )
      }
      runPipeline(data)
      await loadStatus()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
      setFile(null)
    }
  }

  return (
    <div className="page">
      <Header
        title="Data Management"
        subtitle="Ingest transaction data and run the analysis pipeline"
      />

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-2">
        <div className="card card-pad">
          <div className="card-title">
            Load Demonstration Case
          </div>
          <p className="small muted">
            A prepared synthetic fraud scenario: stolen funds
            move from victims through collector accounts to a
            hub (AC381), then branch to cash-out mules —
            embedded in ~900 ordinary accounts.
          </p>
          <button
            className="btn btn-primary"
            onClick={loadDemo}
            disabled={uploading}
          >
            {uploading ? <span className="spin" /> : null}
            Load Demonstration Case
          </button>
        </div>

        <div className="card card-pad">
          <div className="card-title">Upload CSV</div>
          <p className="small muted">
            Required columns: transaction_id, sender_account,
            receiver_account, amount, timestamp,
            transaction_type, channel, sender_location,
            receiver_location. Optional: device_id, ip_hash,
            merchant_id, cashout_location.
          </p>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            style={{ marginBottom: 12 }}
            onChange={(e) =>
              setFile(e.target.files?.[0] || null)
            }
          />
          <button
            className="btn"
            onClick={upload}
            disabled={!file || uploading}
          >
            {uploading ? <span className="spin" /> : null}
            Upload &amp; Analyse
          </button>
        </div>
      </div>

      {pipeline && (
        <div className="card card-pad mt-2">
          <div className="card-title">Processing Pipeline</div>
          <div className="pipeline-steps">
            {pipeline.steps.map((s, i) => (
              <div
                key={s.label}
                className={`pipeline-step ${
                  pipeline.done || i < pipeline.step
                    ? 'done'
                    : i === pipeline.step ? 'active' : ''
                }`}
              >
                <span className="step-icon">
                  {pipeline.done || i < pipeline.step
                    ? '✓'
                    : i === pipeline.step
                      ? '◔'
                      : '○'}
                </span>
                <div>
                  <strong>{s.label}</strong>
                  {(pipeline.done || i < pipeline.step) && (
                    <div className="small muted">
                      {s.detail}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          {pipeline.done && (
            <div className="alert-banner success mt-2">
              <span>✓</span>
              <span>
                Analysis complete. Dashboard, network and
                priority views are updated.
              </span>
            </div>
          )}
        </div>
      )}

      {status && (
        <div className="card card-pad mt-2">
          <div className="card-title">Current Dataset</div>
          {status.loaded ? (
            <div className="grid grid-4">
              <div className="small">
                <div className="muted">Dataset</div>
                <strong>{status.dataset.name}</strong>
              </div>
              <div className="small">
                <div className="muted">Transactions</div>
                <strong>{status.transactions}</strong>
              </div>
              <div className="small">
                <div className="muted">Accounts</div>
                <strong>{status.accounts}</strong>
              </div>
              <div className="small">
                <div className="muted">Detection</div>
                <strong>{status.detection_method}</strong>
              </div>
            </div>
          ) : (
            <EmptyState
              icon="⇪"
              title="No data loaded"
              desc={status.message}
            />
          )}
        </div>
      )}

      <div className="disclaimer">
        CSV validation is performed server-side: structure,
        amounts, timestamps, duplicates and self-transfers
        are checked. Invalid records are flagged, never
        silently dropped.
      </div>
    </div>
  )
}

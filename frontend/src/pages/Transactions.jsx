import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Header from '../components/Header'
import RiskBadge from '../components/RiskBadge'
import DataTable from '../components/DataTable'
import { EmptyState, LoadingState, ErrorState } from '../components/States'
import { formatINR, formatDateTime } from '../api/client'

export default function Transactions() {
  const { api } = useAuth()
  const navigate = useNavigate()
  const [state, setState] = useState({
    transactions: [], total: 0,
  })
  const [filters, setFilters] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [offset, setOffset] = useState(0)
  const [selected, setSelected] = useState(null)
  const limit = 25

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const q = new URLSearchParams({
        limit: String(limit),
        offset: String(offset),
      })
      for (const [k, v] of Object.entries(filters)) {
        if (v !== '' && v !== null && v !== undefined) {
          q.set(k, v)
        }
      }
      const d = await api(`/api/transactions?${q}`)
      setState(d)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [api, filters, offset])

  useEffect(() => { load() }, [load])

  const setFilter = (key, value) => {
    setFilters((f) => ({ ...f, [key]: value }))
    setOffset(0)
  }

  const totalPages = Math.ceil(state.total / limit)

  return (
    <div className="page">
      <Header
        title="Transaction Explorer"
        subtitle={`${state.total.toLocaleString()} transactions`}
      />

      {error && (
        <div className="alert-banner error">
          <span>⚠</span>
          <span>{error}</span>
        </div>
      )}

      <div className="card card-pad mb-2">
        <div className="row" style={{ flexWrap: 'wrap' }}>
          <div className="field" style={{ width: 160, marginBottom: 0 }}>
            <label>Sender</label>
            <input
              className="input mono"
              value={filters.sender || ''}
              onChange={(e) =>
                setFilter('sender', e.target.value)
              }
              placeholder="AC…"
            />
          </div>
          <div className="field" style={{ width: 160, marginBottom: 0 }}>
            <label>Receiver</label>
            <input
              className="input mono"
              value={filters.receiver || ''}
              onChange={(e) =>
                setFilter('receiver', e.target.value)
              }
              placeholder="AC…"
            />
          </div>
          <div className="field" style={{ width: 130, marginBottom: 0 }}>
            <label>Channel</label>
            <select
              className="select"
              value={filters.channel || ''}
              onChange={(e) =>
                setFilter('channel', e.target.value)
              }
            >
              <option value="">All</option>
              <option value="upi">UPI</option>
              <option value="neft">NEFT</option>
              <option value="imps">IMPS</option>
              <option value="bank_transfer">Bank</option>
              <option value="pos">POS</option>
              <option value="atm">ATM</option>
            </select>
          </div>
          <div className="field" style={{ width: 130, marginBottom: 0 }}>
            <label>Type</label>
            <select
              className="select"
              value={filters.tx_type || ''}
              onChange={(e) =>
                setFilter('tx_type', e.target.value)
              }
            >
              <option value="">All</option>
              <option value="transfer">Transfer</option>
              <option value="payment">Payment</option>
              <option value="p2p">P2P</option>
              <option value="merchant">Merchant</option>
              <option value="atm_withdrawal">ATM</option>
              <option value="salary">Salary</option>
            </select>
          </div>
          <div className="field" style={{ width: 120, marginBottom: 0 }}>
            <label>Min ₹</label>
            <input
              className="input"
              type="number"
              value={filters.min_amount || ''}
              onChange={(e) =>
                setFilter('min_amount', e.target.value)
              }
            />
          </div>
          <div className="field" style={{ width: 120, marginBottom: 0 }}>
            <label>Max ₹</label>
            <input
              className="input"
              type="number"
              value={filters.max_amount || ''}
              onChange={(e) =>
                setFilter('max_amount', e.target.value)
              }
            />
          </div>
          <div className="field" style={{ width: 120, marginBottom: 0 }}>
            <label>Risk</label>
            <select
              className="select"
              value={filters.risk || ''}
              onChange={(e) =>
                setFilter('risk', e.target.value)
              }
            >
              <option value="">All</option>
              <option value="high">High+</option>
              <option value="medium">Medium+</option>
            </select>
          </div>
          <button
            className="btn"
            onClick={() => { setFilters({}); setOffset(0) }}
          >
            Clear
          </button>
        </div>
      </div>

      {loading ? (
        <LoadingState label="Loading transactions…" />
      ) : (
        <>
          <div className="card">
            <DataTable
              columns={[
                { key: 'transaction_id', label: 'Transaction' },
                { key: 'timestamp', label: 'Time',
                  render: (v) => formatDateTime(v) },
                { key: 'sender_account', label: 'Sender',
                  render: (v) => <span className="mono">{v}</span> },
                { key: 'receiver_account', label: 'Receiver',
                  render: (v) => <span className="mono">{v}</span> },
                { key: 'amount', label: 'Amount', className: 'num',
                  render: (v) => formatINR(v) },
                { key: 'channel', label: 'Channel' },
                { key: 'sender_risk', label: 'Sender risk',
                  render: (v) => <RiskBadge score={v} short /> },
                { key: 'receiver_risk', label: 'Receiver risk',
                  render: (v) => <RiskBadge score={v} short /> },
              ]}
              rows={state.transactions.map((t, i) => ({
                ...t, id: t.transaction_id || i,
              }))}
              onRowClick={(row) => setSelected(row)}
              emptyMessage="No transactions match the filters."
            />
          </div>
          {totalPages > 1 && (
            <div className="row-between mt-2">
              <span className="small muted">
                Page {Math.floor(offset / limit) + 1} of {totalPages}
              </span>
              <div className="row">
                <button
                  className="btn btn-sm"
                  disabled={offset === 0}
                  onClick={() =>
                    setOffset(Math.max(0, offset - limit))
                  }
                >← Prev</button>
                <button
                  className="btn btn-sm"
                  disabled={offset + limit >= state.total}
                  onClick={() => setOffset(offset + limit)}
                >Next →</button>
              </div>
            </div>
          )}
        </>
      )}

      {selected && (
        <TransactionDetailModal
          tx={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}

function TransactionDetailModal({ tx, onClose }) {
  const { api } = useAuth()
  const navigate = useNavigate()
  const [detail, setDetail] = useState(tx)
  const [error, setError] = useState('')

  useEffect(() => {
    api(`/api/transactions/${tx.transaction_id}`)
      .then(setDetail)
      .catch((e) => setError(e.message))
  }, [api, tx.transaction_id])

  const traceThis = async () => {
    try {
      const r = await api('/api/trails/trace', {
        method: 'POST',
        body: JSON.stringify({
          source: detail.sender_account,
        }),
      })
      navigate('/money-trail', { state: { trail: r } })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(15,23,42,0.45)',
        display: 'flex', alignItems: 'center',
        justifyContent: 'center', zIndex: 100,
      }}
      onClick={onClose}
    >
      <div
        className="card card-pad"
        style={{ width: 640, maxHeight: '85vh', overflow: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="row-between mb-2">
          <div className="card-title" style={{ margin: 0 }}>
            Transaction {detail.transaction_id}
          </div>
          <button className="btn btn-sm" onClick={onClose}>✕</button>
        </div>
        {error && (
          <div className="alert-banner error">
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}
        <div className="grid grid-3 mb-2">
          <div className="small">
            <div className="muted">Amount</div>
            <strong>{formatINR(detail.amount)}</strong>
          </div>
          <div className="small">
            <div className="muted">Time</div>
            <strong>{formatDateTime(detail.timestamp)}</strong>
          </div>
          <div className="small">
            <div className="muted">Channel</div>
            <strong>{detail.channel}</strong>
          </div>
          <div className="small">
            <div className="muted">From</div>
            <span className="mono">{detail.sender_account}</span>{' '}
            <RiskBadge score={detail.sender_risk} short />
          </div>
          <div className="small">
            <div className="muted">To</div>
            <span className="mono">{detail.receiver_account}</span>{' '}
            <RiskBadge score={detail.receiver_risk} short />
          </div>
          <div className="small">
            <div className="muted">Type</div>
            <strong>{detail.transaction_type}</strong>
          </div>
        </div>

        {detail.preceding?.length > 0 && (
          <>
            <div className="small muted mb-1">
              Preceding transactions
            </div>
            <div className="table-wrap mb-2">
              <table className="data-table">
                <tbody>
                  {detail.preceding.map((p, i) => (
                    <tr key={i}>
                      <td>{formatDateTime(p.timestamp)}</td>
                      <td className="mono">{p.sender_account}</td>
                      <td>→</td>
                      <td className="mono">{p.receiver_account}</td>
                      <td className="num">{formatINR(p.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        {detail.following?.length > 0 && (
          <>
            <div className="small muted mb-1">
              Following transactions
            </div>
            <div className="table-wrap mb-2">
              <table className="data-table">
                <tbody>
                  {detail.following.map((p, i) => (
                    <tr key={i}>
                      <td>{formatDateTime(p.timestamp)}</td>
                      <td className="mono">{p.sender_account}</td>
                      <td>→</td>
                      <td className="mono">{p.receiver_account}</td>
                      <td className="num">{formatINR(p.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <button className="btn btn-primary" onClick={traceThis}>
          ⇢ Trace this transaction
        </button>
      </div>
    </div>
  )
}

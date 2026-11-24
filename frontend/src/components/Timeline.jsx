import { formatDateTime } from '../api/client'

/**
 * Timeline — chronological transaction list.
 * items: [{timestamp, sender_account, receiver_account,
 *          amount, transaction_type, suspicious}]
 */
export default function Timeline({ items = [] }) {
  if (!items.length) {
    return (
      <div className="small muted">
        No transactions in the selected window.
      </div>
    )
  }
  return (
    <div className="timeline">
      {items.map((item, i) => (
        <div
          key={i}
          className={`timeline-item ${
            item.suspicious ? 'suspicious' : ''
          }`}
        >
          <div className="timeline-time">
            {formatDateTime(item.timestamp)}
          </div>
          <div className="timeline-body">
            <strong>{item.sender_account}</strong>
            <span className="timeline-arrow">→</span>
            <strong>{item.receiver_account}</strong>
            <span className="muted">
              {' '}· {item.transaction_type}
            </span>
            <div className="mt-1">
              <strong>₹{Number(item.amount).toLocaleString('en-IN')}</strong>
              {item.note && (
                <span className="small muted"> — {item.note}</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

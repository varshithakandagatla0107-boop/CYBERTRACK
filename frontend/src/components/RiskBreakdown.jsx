/**
 * RiskBreakdown — "Why this score?" contributor bars.
 * contributors: [[name, points], ...]
 */
const LABELS = {
  pass_through: 'Rapid pass-through',
  velocity: 'High transaction velocity',
  centrality: 'Network centrality',
  counterparty_diversity: 'Counterparty diversity',
  burst: 'Transaction burst',
  temporal_concentration: 'Temporal concentration',
  ml_anomaly: 'Anomaly signal',
}

export default function RiskBreakdown({
  contributors = [], total,
}) {
  const entries = Array.isArray(contributors)
    ? contributors
    : Object.entries(contributors || {})
  const max = Math.max(1, ...entries.map(([, v]) => Number(v)))

  return (
    <div>
      {entries
        .sort((a, b) => Number(b[1]) - Number(a[1]))
        .map(([key, value]) => (
          <div key={key} className="contributor-row">
            <span className="contributor-name">
              {LABELS[key] || key}
            </span>
            <span className="contributor-bar">
              <span
                className="contributor-fill"
                style={{
                  width: `${(Number(value) / max) * 100}%`,
                  background:
                    Number(value) >= 12
                      ? 'var(--red)'
                      : 'var(--blue)',
                }}
              />
            </span>
            <span className="contributor-val">
              +{Number(value).toFixed(0)}
            </span>
          </div>
        ))}
      <div className="divider" />
      <div className="row-between small">
        <span className="muted">Total risk score</span>
        <strong>{total}</strong>
      </div>
    </div>
  )
}

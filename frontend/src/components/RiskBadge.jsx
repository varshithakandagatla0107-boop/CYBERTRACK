export default function RiskBadge({ score, category, short }) {
  const cat = category ||
    (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low')
  const map = {
    high: { cls: 'badge-high', label: 'HIGH RISK' },
    medium: { cls: 'badge-medium', label: 'MEDIUM RISK' },
    low: { cls: 'badge-low', label: 'LOW RISK' },
    unreviewed: { cls: 'badge-neutral', label: 'UNREVIEWED' },
  }
  const { cls, label } = map[cat] || map.low
  return (
    <span className={`badge ${cls}`} title={`Risk score: ${score}`}>
      {short ? `${score}` : `${score} · ${label}`}
    </span>
  )
}

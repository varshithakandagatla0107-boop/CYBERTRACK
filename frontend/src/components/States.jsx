export function EmptyState({
  icon = '◌', title, desc, action,
}) {
  return (
    <div className="state-box">
      <div className="icon">{icon}</div>
      <div className="title">{title}</div>
      <div className="desc">{desc}</div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="state-box">
      <div className="spin"
        style={{ width: 26, height: 26, margin: '0 auto 12px' }}
      />
      <div className="desc">{label}</div>
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state-box">
      <div className="icon" style={{ color: 'var(--red)' }}>⚠</div>
      <div className="title">Something went wrong</div>
      <div className="desc">{message}</div>
      {onRetry && (
        <div className="mt-2">
          <button className="btn" onClick={onRetry}>Retry</button>
        </div>
      )}
    </div>
  )
}

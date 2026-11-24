export default function Header({ title, subtitle, children }) {
  return (
    <header className="topbar">
      <div>
        <div className="topbar-title">{title}</div>
        {subtitle && (
          <div className="small muted">{subtitle}</div>
        )}
      </div>
      {children && <div className="topbar-right">{children}</div>}
    </header>
  )
}

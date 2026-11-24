import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '▦' },
  { to: '/investigations', label: 'Investigations', icon: '▤' },
  { to: '/network', label: 'Network Explorer', icon: '◎' },
  { to: '/money-trail', label: 'Money Trail', icon: '⇢' },
  { to: '/priority', label: 'Priority Accounts', icon: '⚑' },
  { to: '/transactions', label: 'Transactions', icon: '≡' },
  { to: '/analytics', label: 'Analytics', icon: '◔' },
  { to: '/alerts', label: 'Alerts', icon: '⚠' },
]

const NAV_ADMIN = [
  { to: '/data', label: 'Data Management', icon: '⇪' },
  { to: '/audit', label: 'Audit Log', icon: '✓' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const navItems = [...NAV, ...NAV_ADMIN]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-name">CYBERTRACK</div>
        <div className="brand-tag">PS-35 · MULE ACCOUNT TRACING</div>
      </div>
      <ul className="nav-list">
        <li className="nav-section">Investigation</li>
        {NAV.map((item) => (
          <li key={item.to} className="nav-item">
            <NavLink
              to={item.to}
              className={({ isActive }) =>
                isActive ? 'active' : ''
              }
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          </li>
        ))}
        <li className="nav-section">System</li>
        {NAV_ADMIN.map((item) => (
          <li key={item.to} className="nav-item">
            <NavLink
              to={item.to}
              className={({ isActive }) =>
                isActive ? 'active' : ''
              }
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
      <div className="sidebar-footer">
        <div className="who">{user?.full_name || user?.investigator_id}</div>
        <div className="role">
          Role: {user?.role || 'investigator'}
        </div>
        <div className="env-badge">PROTOTYPE · SYNTHETIC DATA</div>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </aside>
  )
}

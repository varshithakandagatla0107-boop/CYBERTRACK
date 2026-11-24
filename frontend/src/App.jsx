import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Investigations from './pages/Investigations'
import InvestigationDetail from './pages/InvestigationDetail'
import NetworkExplorer from './pages/NetworkExplorer'
import MoneyTrail from './pages/MoneyTrail'
import PriorityAccounts from './pages/PriorityAccounts'
import Transactions from './pages/Transactions'
import Analytics from './pages/Analytics'
import Alerts from './pages/Alerts'
import DataManagement from './pages/DataManagement'
import AuditLog from './pages/AuditLog'
import Settings from './pages/Settings'
import AccountDetail from './pages/AccountDetail'

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  const location = useLocation()
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return children
}

function AppLayout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-area">{children}</div>
    </div>
  )
}

export default function App() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={
        user ? <Navigate to="/dashboard" replace /> : <Login />
      } />
      <Route path="/" element={
        <ProtectedRoute>
          <AppLayout>
            <Dashboard />
          </AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AppLayout><Dashboard /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/investigations" element={
        <ProtectedRoute>
          <AppLayout><Investigations /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/investigations/:id" element={
        <ProtectedRoute>
          <AppLayout><InvestigationDetail /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/network" element={
        <ProtectedRoute>
          <AppLayout><NetworkExplorer /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/money-trail" element={
        <ProtectedRoute>
          <AppLayout><MoneyTrail /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/priority" element={
        <ProtectedRoute>
          <AppLayout><PriorityAccounts /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/transactions" element={
        <ProtectedRoute>
          <AppLayout><Transactions /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/analytics" element={
        <ProtectedRoute>
          <AppLayout><Analytics /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/alerts" element={
        <ProtectedRoute>
          <AppLayout><Alerts /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/data" element={
        <ProtectedRoute>
          <AppLayout><DataManagement /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/audit" element={
        <ProtectedRoute>
          <AppLayout><AuditLog /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <AppLayout><Settings /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="/account/:accountId" element={
        <ProtectedRoute>
          <AppLayout><AccountDetail /></AppLayout>
        </ProtectedRoute>
      } />
      <Route path="*" element={
        <Navigate to="/dashboard" replace />
      } />
    </Routes>
  )
}

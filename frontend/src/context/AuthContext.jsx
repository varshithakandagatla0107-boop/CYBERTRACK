import { createContext, useContext, useEffect, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('cybertrack_session')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) {
      localStorage.setItem('cybertrack_session', JSON.stringify(user))
    } else {
      localStorage.removeItem('cybertrack_session')
    }
  }, [user])

  const login = async (investigatorId, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        investigator_id: investigatorId,
        password,
      }),
    })
    const data = await res.json()
    if (!res.ok) {
      throw new Error(data.detail || 'Login failed')
    }
    setUser({ token: data.token, ...data.user })
    return data
  }

  const logout = () => setUser(null)

  const api = async (path, options = {}) => {
    const res = await fetch(path, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(user?.token
          ? { Authorization: `Bearer ${user.token}` }
          : {}),
        ...(options.headers || {}),
      },
    })
    if (res.status === 401) {
      setUser(null)
      throw new Error('Session expired. Please log in again.')
    }
    const text = await res.text()
    let data = null
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = { message: text }
    }
    if (!res.ok) {
      throw new Error(
        data?.detail || data?.message || `Request failed (${res.status})`
      )
    }
    return data
  }

  return (
    <AuthContext.Provider
      value={{ user, login, logout, api }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

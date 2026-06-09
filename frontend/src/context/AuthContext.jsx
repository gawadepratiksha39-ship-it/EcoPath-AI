/**
 * AuthContext.jsx — Global authentication state (JWT in localStorage).
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { login as apiLogin, register as apiRegister, fetchMe, setAuthToken } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('ecopath_token')
    if (!token) {
      setLoading(false)
      return
    }
    setAuthToken(token)
    try {
      const data = await fetchMe()
      setUser(data.user)
      setStats(data.stats)
    } catch {
      localStorage.removeItem('ecopath_token')
      setAuthToken(null)
      setUser(null)
      setStats(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = async (email, password) => {
    const data = await apiLogin(email, password)
    localStorage.setItem('ecopath_token', data.token)
    setAuthToken(data.token)
    setUser(data.user)
    const me = await fetchMe()
    setStats(me.stats)
    return data.user
  }

  const register = async (name, email, password) => {
    const data = await apiRegister(name, email, password)
    localStorage.setItem('ecopath_token', data.token)
    setAuthToken(data.token)
    setUser(data.user)
    setStats({ trip_count: 0, total_distance_km: 0, total_carbon_kg: 0 })
    return data.user
  }

  const logout = () => {
    localStorage.removeItem('ecopath_token')
    setAuthToken(null)
    setUser(null)
    setStats(null)
  }

  return (
    <AuthContext.Provider value={{ user, stats, loading, login, register, logout, refreshUser: loadUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

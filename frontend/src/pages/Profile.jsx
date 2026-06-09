/**
 * Profile.jsx — User profile with AI sustainability summary.
 */
import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import SustainabilityInsights from '../components/SustainabilityInsights'
import { getAIInsights } from '../services/api'

function Profile() {
  const { user, stats } = useAuth()
  const [aiInsights, setAiInsights] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAIInsights()
      .then(setAiInsights)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <header className="page-header">
        <h1>Your Profile</h1>
        <p>Account details and AI-powered eco-travel summary</p>
      </header>

      <div className="grid-2">
        <div className="card">
          <h2 className="card-title">Account</h2>
          <div className="profile-field">
            <span className="stat-label">Name</span>
            <span className="stat-value">{user?.name}</span>
          </div>
          <div className="profile-field">
            <span className="stat-label">Email</span>
            <span className="stat-value">{user?.email}</span>
          </div>
          {user?.created_at && (
            <div className="profile-field">
              <span className="stat-label">Member since</span>
              <span className="stat-value">
                {new Date(user.created_at + 'Z').toLocaleDateString()}
              </span>
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="card-title">Your Impact</h2>
          <div className="stat-grid">
            <div className="stat-item">
              <span className="stat-label">Total Trips</span>
              <span className="stat-value">{stats?.trip_count ?? 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Distance Traveled</span>
              <span className="stat-value">{stats?.total_distance_km ?? 0} km</span>
            </div>
            <div className="stat-item stat-highlight">
              <span className="stat-label">Total Carbon</span>
              <span className="carbon-value">{stats?.total_carbon_kg ?? 0}</span>
              <span className="carbon-unit"> kg CO₂</span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <SustainabilityInsights insights={aiInsights} loading={loading} />
      </div>
    </div>
  )
}

export default Profile

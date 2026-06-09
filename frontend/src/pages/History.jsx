/**
 * History.jsx — Trip history with AI sustainability dashboard.
 */
import { useState, useEffect } from 'react'
import Dashboard from '../components/Dashboard'
import SustainabilityInsights from '../components/SustainabilityInsights'
import { getCarbonHistory, getAIInsights } from '../services/api'

function History() {
  const [records, setRecords] = useState([])
  const [stats, setStats] = useState(null)
  const [aiInsights, setAiInsights] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([getCarbonHistory(), getAIInsights()])
      .then(([{ records: r, stats: s }, ai]) => {
        setRecords(r)
        setStats(s)
        setAiInsights(ai)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div>
        <header className="page-header">
          <h1>Your Carbon History</h1>
        </header>
        <p className="loading-text">Loading history...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <header className="page-header">
          <h1>Your Carbon History</h1>
        </header>
        <div className="form-error" role="alert">{error}</div>
      </div>
    )
  }

  return (
    <div>
      <header className="page-header">
        <h1>Your Carbon History</h1>
        <p>Review past trips and AI-powered sustainability analytics.</p>
      </header>

      <SustainabilityInsights insights={aiInsights} />

      {stats && (
        <div className="stats-banner" style={{ marginTop: '1.5rem' }}>
          <div className="stats-banner-item">
            <strong>{stats.trip_count}</strong>
            <span>Trips</span>
          </div>
          <div className="stats-banner-item">
            <strong>{stats.total_distance_km}</strong>
            <span>km traveled</span>
          </div>
          <div className="stats-banner-item">
            <strong>{stats.total_carbon_kg}</strong>
            <span>kg CO₂ total</span>
          </div>
        </div>
      )}

      <div style={{ marginTop: '1.5rem' }}>
        <Dashboard records={records} />
      </div>
    </div>
  )
}

export default History

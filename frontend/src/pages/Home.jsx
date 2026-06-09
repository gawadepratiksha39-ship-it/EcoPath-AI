/**
 * Home.jsx — India route planner with AI sustainability insights.
 */
import { useState, useEffect, useRef } from 'react'
import RouteForm from '../components/RouteForm'
import MapView from '../components/MapView'
import CarbonCard from '../components/CarbonCard'
import AIInsightsCard from '../components/AIInsightsCard'
import RouteComparison from '../components/RouteComparison'
import { testConnection, planRoute } from '../services/api'
import { useAuth } from '../context/AuthContext'

const LOADING_PHASES = [
  { at: 0, message: 'Searching locations...' },
  { at: 2500, message: 'Calculating route...' },
  { at: 6000, message: 'Generating AI insights...' },
]

function Home() {
  const { user, refreshUser } = useAuth()
  const [apiStatus, setApiStatus] = useState(null)
  const [routeResult, setRouteResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingPhase, setLoadingPhase] = useState('')
  const [error, setError] = useState(null)
  const phaseTimers = useRef([])

  useEffect(() => {
    testConnection()
      .then((data) => setApiStatus({ ok: true, message: data.message }))
      .catch(() => setApiStatus({ ok: false, message: 'Backend unreachable' }))
  }, [])

  const clearPhaseTimers = () => {
    phaseTimers.current.forEach(clearTimeout)
    phaseTimers.current = []
  }

  const startLoadingPhases = () => {
    clearPhaseTimers()
    LOADING_PHASES.forEach(({ at, message }) => {
      const id = setTimeout(() => setLoadingPhase(message), at)
      phaseTimers.current.push(id)
    })
  }

  const handleRouteSubmit = async (data) => {
    if (data.error) {
      setError(data.error)
      return
    }

    setLoading(true)
    setError(null)
    setRouteResult(null)
    startLoadingPhases()
    setLoadingPhase(LOADING_PHASES[0].message)

    try {
      const result = await planRoute(
        data.source,
        data.destination,
        data.transportMode,
        data.sourcePlace,
        data.destPlace,
      )
      setRouteResult(result)
      refreshUser()
    } catch (err) {
      setRouteResult(null)
      setError(err.message)
    } finally {
      clearPhaseTimers()
      setLoading(false)
      setLoadingPhase('')
    }
  }

  const ai = routeResult?.ai_insights

  return (
    <div>
      <header className="page-header">
        <h1>Plan Your Eco-Friendly Route in India</h1>
        <p>
          Welcome back, {user?.name?.split(' ')[0]}! Type any Indian location
          and get AI-powered sustainability insights.
        </p>
        {apiStatus && (
          <span className={`status-badge ${apiStatus.ok ? 'ok' : 'error'}`}>
            {apiStatus.ok ? '✓ ' : '✗ '}
            {apiStatus.message}
          </span>
        )}
      </header>

      <div className="grid-2">
        <RouteForm
          onSubmit={handleRouteSubmit}
          loading={loading}
          loadingPhase={loadingPhase}
          error={error}
          resolvedRoute={routeResult}
        />
        <CarbonCard routeResult={routeResult} loading={loading} loadingPhase={loadingPhase} />
      </div>

      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        <AIInsightsCard insights={ai} loading={loading} loadingPhase={loadingPhase} />
        <RouteComparison
          comparison={ai?.route_comparison}
          bestMode={ai?.recommended_mode}
          currentMode={routeResult?.transport_mode}
        />
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <MapView route={routeResult} />
      </div>
    </div>
  )
}

export default Home

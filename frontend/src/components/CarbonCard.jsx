/**
 * CarbonCard.jsx — Displays route stats: distance, travel time, CO₂ emissions.
 */

const MODE_LABELS = {
  car: 'Car',
  bus: 'Bus',
  train: 'Train',
  bicycle: 'Bicycle',
  walking: 'Walking',
}

function formatDuration(minutes) {
  if (minutes == null) return '—'
  if (minutes < 60) return `${minutes} min`
  const hrs = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return mins > 0 ? `${hrs} hr ${mins} min` : `${hrs} hr`
}

function CarbonCard({ routeResult = null, loading = false, loadingPhase = '' }) {
  const mode = routeResult?.transport_mode || 'car'
  const modeLabel = MODE_LABELS[mode] || mode

  if (loading) {
    return (
      <div className="card">
        <h2 className="card-title">Trip Summary</h2>
        <p className="loading-text">{loadingPhase || 'Calculating route...'}</p>
      </div>
    )
  }

  if (!routeResult) {
    return (
      <div className="card">
        <h2 className="card-title">Trip Summary</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>
          Enter a route to see distance, travel time, and carbon emissions.
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="card-title">Trip Summary</h2>

      <div className="stat-grid">
        <div className="stat-item">
          <span className="stat-label">Distance</span>
          <span className="stat-value">{routeResult.distance_km} km</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Travel Time</span>
          <span className="stat-value">
            {formatDuration(routeResult.duration_min)}
          </span>
        </div>
        <div className="stat-item stat-highlight">
          <span className="stat-label">Carbon Emission</span>
          <span className="carbon-value">{routeResult.carbon_kg}</span>
          <span className="carbon-unit"> kg CO₂</span>
        </div>
      </div>

      <p className="mode-badge">Mode: {modeLabel}</p>
    </div>
  )
}

export default CarbonCard

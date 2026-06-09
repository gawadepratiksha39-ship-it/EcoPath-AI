/**
 * RouteComparison.jsx — AI-powered multi-mode emission comparison.
 */
const MODE_ICONS = {
  car: '🚗',
  bus: '🚌',
  train: '🚆',
  bicycle: '🚲',
  walking: '🚶',
}

function RouteComparison({ comparison = [], bestMode = null, currentMode = null }) {
  if (!comparison?.length) return null

  return (
    <div className="card">
      <h2 className="card-title">Route Comparison AI</h2>
      <p className="card-subtitle">
        Estimated CO₂ emissions by transport mode for this route
      </p>

      <div className="comparison-grid">
        {comparison.map((item) => (
          <div
            key={item.mode}
            className={[
              'comparison-item',
              item.is_best ? 'comparison-best' : '',
              item.is_current ? 'comparison-current' : '',
            ].filter(Boolean).join(' ')}
          >
            <span className="comparison-icon">{MODE_ICONS[item.mode] || '🚗'}</span>
            <span className="comparison-label">{item.label}</span>
            <span className="comparison-carbon">{item.carbon_kg} kg</span>
            <span className="comparison-pct">
              {item.reduction_vs_car_pct}% vs car
            </span>
            {item.is_best && <span className="comparison-tag">Best</span>}
            {item.is_current && <span className="comparison-tag current">Your choice</span>}
          </div>
        ))}
      </div>
    </div>
  )
}

export default RouteComparison

/**
 * AIInsightsCard.jsx — Rule-based AI eco recommendations and eco score.
 */
function BadgeDisplay({ badge }) {
  const cls = {
    'Green Champion': 'badge-green',
    Gold: 'badge-gold',
    Silver: 'badge-silver',
    Bronze: 'badge-bronze',
  }[badge] || 'badge-bronze'

  return <span className={`sustainability-badge ${cls}`}>{badge}</span>
}

function AIInsightsCard({ insights = null, loading = false, loadingPhase = '' }) {
  if (loading) {
    return (
      <div className="card ai-card">
        <h2 className="card-title">AI Insights</h2>
        <p className="loading-text">{loadingPhase || 'Analyzing sustainability...'}</p>
      </div>
    )
  }

  if (!insights) {
    return (
      <div className="card ai-card">
        <h2 className="card-title">AI Insights</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>
          Plan a route to receive intelligent eco recommendations powered by our AI engine.
        </p>
      </div>
    )
  }

  const scoreColor = insights.eco_score_color || '#40916c'

  return (
    <div className="card ai-card">
      <div className="ai-card-header">
        <h2 className="card-title">AI Insights</h2>
        <BadgeDisplay badge={insights.badge} />
      </div>

      <div className="eco-score-block">
        <div
          className="eco-score-ring"
          style={{ '--score': insights.eco_score, '--score-color': scoreColor }}
        >
          <span className="eco-score-number">{insights.eco_score}</span>
        </div>
        <div className="eco-score-meta">
          <strong>Eco Score</strong>
          <span className="eco-score-label" style={{ color: scoreColor }}>
            {insights.eco_score_label}
          </span>
          <p>{insights.eco_score_explanation}</p>
        </div>
      </div>

      <div className="ai-highlight">
        <span className="stat-label">Recommended Mode</span>
        <strong>{insights.recommended_mode_label}</strong>
        {insights.emissions_saved_kg > 0 && (
          <span className="ai-savings">
            Save up to {insights.emissions_saved_kg} kg CO₂ ({insights.co2_reduction_pct}%)
          </span>
        )}
      </div>

      <p className="ai-explanation">{insights.explanation}</p>

      {insights.recommendations?.length > 0 && (
        <ul className="ai-recommendations">
          {insights.recommendations.map((rec, i) => (
            <li key={i} className={`ai-rec ai-rec-${rec.priority}`}>
              <strong>{rec.title}</strong>
              <p>{rec.explanation}</p>
              {rec.savings_kg > 0 && (
                <span className="ai-rec-savings">
                  Potential savings: {rec.savings_kg} kg CO₂ ({rec.savings_pct}%)
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default AIInsightsCard

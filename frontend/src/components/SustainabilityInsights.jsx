/**
 * SustainabilityInsights.jsx — Dashboard AI sustainability section.
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

function SustainabilityInsights({ insights = null, loading = false }) {
  if (loading) {
    return (
      <div className="card ai-card">
        <h2 className="card-title">AI Sustainability Insights</h2>
        <p className="loading-text">Loading insights...</p>
      </div>
    )
  }

  if (!insights) return null

  const scoreColor = insights.eco_score_color || '#40916c'

  return (
    <section className="sustainability-section">
      <h2 className="section-title">AI Sustainability Insights</h2>

      <div className="grid-2">
        <div className="card ai-card">
          <div className="ai-card-header">
            <h3 className="card-title">Your Eco Performance</h3>
            <BadgeDisplay badge={insights.badge} />
          </div>

          <div className="eco-score-block">
            <div
              className="eco-score-ring"
              style={{ '--score': insights.overall_eco_score ?? insights.eco_score, '--score-color': scoreColor }}
            >
              <span className="eco-score-number">{insights.overall_eco_score ?? insights.eco_score}</span>
            </div>
            <div className="eco-score-meta">
              <strong>Overall Eco Score</strong>
              <p>{insights.eco_score_explanation || insights.explanation}</p>
            </div>
          </div>

          <p className="ai-explanation">{insights.explanation}</p>
        </div>

        <div className="card">
          <h3 className="card-title">Impact Summary</h3>
          <div className="stat-grid">
            <div className="stat-item">
              <span className="stat-label">Total CO₂ Saved</span>
              <span className="stat-value">{insights.total_emissions_saved_kg} kg</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Most Used Mode</span>
              <span className="stat-value">{insights.most_used_mode_label}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Recommended Next</span>
              <span className="stat-value">{insights.recommended_mode_label}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="period-grid">
        <div className="card period-card">
          <h3 className="card-title">Weekly Performance</h3>
          <div className="period-stats">
            <div><strong>{insights.weekly?.trips ?? 0}</strong><span>Trips</span></div>
            <div><strong>{insights.weekly?.distance_km ?? 0}</strong><span>km</span></div>
            <div><strong>{insights.weekly?.carbon_kg ?? 0}</strong><span>kg CO₂</span></div>
            <div><strong>{insights.weekly?.eco_score ?? 0}</strong><span>Eco Score</span></div>
          </div>
        </div>
        <div className="card period-card">
          <h3 className="card-title">Monthly Summary</h3>
          <div className="period-stats">
            <div><strong>{insights.monthly?.trips ?? 0}</strong><span>Trips</span></div>
            <div><strong>{insights.monthly?.distance_km ?? 0}</strong><span>km</span></div>
            <div><strong>{insights.monthly?.carbon_kg ?? 0}</strong><span>kg CO₂</span></div>
            <div><strong>{insights.monthly?.eco_score ?? 0}</strong><span>Eco Score</span></div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default SustainabilityInsights

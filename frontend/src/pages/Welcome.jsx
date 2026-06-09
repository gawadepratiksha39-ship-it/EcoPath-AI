/**
 * Welcome.jsx — Public landing page with product overview and CTAs.
 */
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  {
    icon: '🗺️',
    title: 'India Route Planner',
    desc: 'Plan eco-friendly routes between Indian cities with live OpenStreetMap visualization.',
  },
  {
    icon: '🌱',
    title: 'Carbon Tracking',
    desc: 'See distance, travel time, and CO₂ emissions for every trip you take.',
  },
  {
    icon: '🤖',
    title: 'AI Eco Insights',
    desc: 'Get intelligent recommendations, eco scores, and mode comparisons powered by our rule-based AI engine.',
  },
  {
    icon: '📊',
    title: 'Trip History',
    desc: 'Review your past journeys and track progress toward lower emissions.',
  },
  {
    icon: '🚌',
    title: 'Multi-Mode Travel',
    desc: 'Compare car, bus, train, bicycle, and walking footprints side by side.',
  },
]

function Welcome() {
  const { user } = useAuth()

  return (
    <div className="welcome-page">
      <section className="hero">
        <div className="hero-content">
          <span className="hero-badge">India&apos;s Climate Action Platform</span>
          <h1>Travel Smarter.<br />Leave a Lighter Footprint.</h1>
          <p>
            EcoPath AI helps you choose sustainable routes across India,
            calculate your carbon emissions, and build greener travel habits.
          </p>
          <div className="hero-actions">
            {user ? (
              <Link to="/planner" className="btn btn-primary btn-lg">
                Go to Route Planner
              </Link>
            ) : (
              <>
                <Link to="/signup" className="btn btn-primary btn-lg">
                  Get Started Free
                </Link>
                <Link to="/login" className="btn btn-outline btn-lg">
                  Log In
                </Link>
              </>
            )}
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-card">
            <p className="hero-card-label">Sample trip</p>
            <h3>Mumbai → Pune</h3>
            <div className="hero-stats">
              <div><strong>148</strong><span>km</span></div>
              <div><strong>31</strong><span>kg CO₂</span></div>
              <div><strong>2h</strong><span>travel</span></div>
            </div>
          </div>
        </div>
      </section>

      <section className="features-section">
        <h2>Everything you need for greener travel</h2>
        <div className="features-grid">
          {FEATURES.map((f) => (
            <div key={f.title} className="feature-card">
              <span className="feature-icon">{f.icon}</span>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="cta-section">
        <h2>Ready to reduce your travel emissions?</h2>
        <p>Join EcoPath AI and start planning sustainable routes today.</p>
        {!user && (
          <Link to="/signup" className="btn btn-primary btn-lg">
            Create Your Account
          </Link>
        )}
      </section>
    </div>
  )
}

export default Welcome

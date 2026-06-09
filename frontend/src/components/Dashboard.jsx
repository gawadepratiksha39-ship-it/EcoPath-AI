/**
 * Dashboard.jsx — Carbon history summary with trip list.
 */

const MODE_LABELS = {
  car: 'Car',
  bus: 'Bus',
  train: 'Train',
  bicycle: 'Bicycle',
  walking: 'Walking',
}

function Dashboard({ records = [] }) {
  return (
    <div className="card">
      <h2 className="card-title">Carbon History</h2>
      {records.length > 0 ? (
        <ul className="history-list">
          {records.map((record) => (
            <li key={record.id} className="history-item">
              <div className="history-route">
                <strong>{record.source}</strong>
                <span className="history-arrow">→</span>
                <strong>{record.destination}</strong>
              </div>
              <div className="history-meta">
                <span>{record.distance_km} km</span>
                <span>{record.carbon_kg} kg CO₂</span>
                <span>{MODE_LABELS[record.transport_mode] || record.transport_mode}</span>
                {record.created_at && (
                  <span className="history-date">
                    {new Date(record.created_at + 'Z').toLocaleDateString()}
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ color: 'var(--color-text-muted)' }}>
          No travel history yet. Plan a route to start tracking your footprint.
        </p>
      )}
    </div>
  )
}

export default Dashboard

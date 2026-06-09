/**
 * RouteForm.jsx — India route input; autocomplete is optional.
 * Typed locations are geocoded automatically on submit.
 */
import { useState } from 'react'
import PlaceInput from './PlaceInput'

/** Use cached coords only when input still matches the selected suggestion */
function coordsIfMatchingInput(text, place) {
  if (!place?.lat) return null
  const t = text.trim().toLowerCase()
  if (!t) return null
  const label = (place.label || place.short_name || '').toLowerCase()
  const city = label.split(',')[0].trim()
  if (t === label || t === city || label.startsWith(t) || city.startsWith(t)) {
    return place
  }
  return null
}

function RouteForm({
  onSubmit,
  loading = false,
  loadingPhase = '',
  error = null,
  resolvedRoute = null,
}) {
  const [source, setSource] = useState('')
  const [destination, setDestination] = useState('')
  const [transportMode, setTransportMode] = useState('car')
  const [sourcePlace, setSourcePlace] = useState(null)
  const [destPlace, setDestPlace] = useState(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!onSubmit || loading) return

    const src = source.trim()
    const dst = destination.trim()

    if (!src || !dst) {
      onSubmit({ error: 'Please enter both source and destination.' })
      return
    }

    if (src.toLowerCase() === dst.toLowerCase()) {
      onSubmit({ error: 'Source and destination must be different.' })
      return
    }

    onSubmit({
      source: src,
      destination: dst,
      transportMode,
      sourcePlace: coordsIfMatchingInput(src, sourcePlace),
      destPlace: coordsIfMatchingInput(dst, destPlace),
    })
  }

  const displaySource =
    resolvedRoute?.source?.short_name || sourcePlace?.short_name || sourcePlace?.label
  const displayDest =
    resolvedRoute?.destination?.short_name || destPlace?.short_name || destPlace?.label

  const buttonLabel = loading
    ? loadingPhase || 'Finding Route...'
    : 'Find Eco Route'

  return (
    <div className="card">
      <h2 className="card-title">Plan Your Route (India)</h2>
      <p className="card-subtitle">
        Type any city, town, village, or landmark — suggestions are optional
      </p>
      <form onSubmit={handleSubmit}>
        <PlaceInput
          id="source"
          label="From"
          placeholder="e.g. Sawantwadi, Mumbai, Goa"
          value={source}
          onChange={setSource}
          onSelect={setSourcePlace}
          selectedPlace={resolvedRoute ? null : sourcePlace}
          disabled={loading}
        />
        <PlaceInput
          id="destination"
          label="To"
          placeholder="e.g. Mapusa, Pune, Jaipur"
          value={destination}
          onChange={setDestination}
          onSelect={setDestPlace}
          selectedPlace={resolvedRoute ? null : destPlace}
          disabled={loading}
        />

        {(displaySource || displayDest) && resolvedRoute && (
          <div className="resolved-locations">
            {displaySource && (
              <p><strong>Source:</strong> {displaySource}</p>
            )}
            {displayDest && (
              <p><strong>Destination:</strong> {displayDest}</p>
            )}
          </div>
        )}

        {loading && loadingPhase && (
          <div className="loading-phase" role="status">
            <span className="loading-spinner-inline" />
            {loadingPhase}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="transport">Transport Mode</label>
          <select
            id="transport"
            value={transportMode}
            onChange={(e) => setTransportMode(e.target.value)}
            disabled={loading}
          >
            <option value="car">Car</option>
            <option value="bus">Bus</option>
            <option value="train">Train</option>
            <option value="bicycle">Bicycle</option>
            <option value="walking">Walking</option>
          </select>
        </div>

        {error && <div className="form-error" role="alert">{error}</div>}

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {buttonLabel}
        </button>
      </form>
    </div>
  )
}

export default RouteForm

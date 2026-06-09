/**
 * MapView.jsx — Leaflet map restricted to India with route display.
 */
import { useEffect } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

const INDIA_CENTER = [22.5937, 78.9629]
const INDIA_ZOOM = 5
const INDIA_BOUNDS = L.latLngBounds(
  L.latLng(6.5, 68),
  L.latLng(37.5, 97.5),
)

const startIcon = new L.Icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  className: 'marker-start',
})

const endIcon = new L.Icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  className: 'marker-end',
})

/** Auto-zoom map to fit the full route */
function FitBounds({ positions }) {
  const map = useMap()

  useEffect(() => {
    if (positions && positions.length > 1) {
      const bounds = L.latLngBounds(positions)
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
    }
  }, [positions, map])

  return null
}

function MapView({ route = null }) {
  const hasRoute = route?.geometry?.length > 0

  const sourcePos = route?.source
    ? [route.source.lat, route.source.lon]
    : null
  const destPos = route?.destination
    ? [route.destination.lat, route.destination.lon]
    : null

  const fitPositions = hasRoute
    ? [...route.geometry, ...(sourcePos ? [sourcePos] : []), ...(destPos ? [destPos] : [])]
    : []

  const sourceLabel = route?.source?.short_name || route?.source?.display_name
  const destLabel = route?.destination?.short_name || route?.destination?.display_name

  return (
    <div className="card map-card">
      <h2 className="card-title">Route Map (India)</h2>
      <div className="map-container">
        <MapContainer
          center={INDIA_CENTER}
          zoom={INDIA_ZOOM}
          className="leaflet-map"
          scrollWheelZoom
          maxBounds={INDIA_BOUNDS}
          maxBoundsViscosity={1.0}
          minZoom={4}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {hasRoute && (
            <>
              <FitBounds positions={fitPositions} />
              <Polyline
                positions={route.geometry}
                color="#2d6a4f"
                weight={5}
                opacity={0.85}
              />
            </>
          )}

          {sourcePos && (
            <Marker position={sourcePos} icon={startIcon}>
              <Popup>
                <strong>Start</strong>
                <br />
                {sourceLabel}
              </Popup>
            </Marker>
          )}

          {destPos && (
            <Marker position={destPos} icon={endIcon}>
              <Popup>
                <strong>Destination</strong>
                <br />
                {destLabel}
              </Popup>
            </Marker>
          )}
        </MapContainer>

        {!hasRoute && (
          <div className="map-overlay-hint">
            Select Indian cities and click &quot;Find Eco Route&quot;
          </div>
        )}
      </div>
    </div>
  )
}

export default MapView

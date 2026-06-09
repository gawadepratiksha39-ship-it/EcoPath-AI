/**
 * api.js — Centralized API client for EcoPath AI backend.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 90000,
})

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common.Authorization
  }
}

function getErrorMessage(error) {
  const serverMsg = error.response?.data?.error
  if (serverMsg) {
    if (serverMsg.includes('valid Indian location')) {
      return `Location not found: ${serverMsg} Try adding a state name (e.g. "Sawantwadi, Maharashtra").`
    }
    if (serverMsg.includes('seem incorrect') || serverMsg.includes('extremely far')) {
      return `${serverMsg} Check spelling or add more detail (city, district, or state).`
    }
    if (serverMsg.includes('No route') || serverMsg.includes('route')) {
      return 'Route unavailable between these locations. Try nearby cities or different transport mode.'
    }
    return serverMsg
  }
  if (error.code === 'ECONNABORTED') {
    return 'Request timed out while searching locations. Please try again.'
  }
  if (error.message === 'Network Error') {
    return 'Network error — cannot reach the server. Check your connection and try again.'
  }
  if (error.response?.status === 503) {
    return 'Geocoding or routing service is temporarily unavailable. Please try again shortly.'
  }
  return error.message || 'Something went wrong. Please try again.'
}

export async function testConnection() {
  const { data } = await api.get('/test')
  return data
}

export async function login(email, password) {
  try {
    const { data } = await api.post('/auth/login', { email, password })
    return data
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}

export async function register(name, email, password) {
  try {
    const { data } = await api.post('/auth/register', { name, email, password })
    return data
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}

export async function fetchMe() {
  const { data } = await api.get('/auth/me')
  return data
}

export async function suggestPlaces(query) {
  try {
    const { data } = await api.get('/routes/suggest', { params: { q: query } })
    return data.suggestions || []
  } catch {
    return []
  }
}

export async function planRoute(source, destination, transportMode, sourcePlace, destPlace) {
  try {
    const { data } = await api.post('/routes/plan', {
      source,
      destination,
      transport_mode: transportMode,
      source_place: sourcePlace
        ? {
            lat: sourcePlace.lat,
            lon: sourcePlace.lon,
            short_name: sourcePlace.short_name || sourcePlace.label,
            display_name: sourcePlace.display_name || sourcePlace.label,
            country_code: 'in',
          }
        : null,
      destination_place: destPlace
        ? {
            lat: destPlace.lat,
            lon: destPlace.lon,
            short_name: destPlace.short_name || destPlace.label,
            display_name: destPlace.display_name || destPlace.label,
            country_code: 'in',
          }
        : null,
    })
    return data
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}

export async function getCarbonHistory() {
  try {
    const { data } = await api.get('/carbon/history')
    return { records: data.records, stats: data.stats }
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}

/** Personalized AI sustainability insights from trip history */
export async function getAIInsights() {
  try {
    const { data } = await api.get('/ai/insights')
    return data
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}

/** Analyze a specific route with the AI engine */
export async function analyzeRouteAI(routeData) {
  try {
    const { data } = await api.post('/ai/analyze', routeData)
    return data
  } catch (error) {
    throw new Error(getErrorMessage(error))
  }
}

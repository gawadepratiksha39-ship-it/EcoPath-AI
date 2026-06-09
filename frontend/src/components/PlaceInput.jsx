/**
 * PlaceInput.jsx — Optional Indian location autocomplete.
 * Users can type freely; geocoding happens on form submit.
 */
import { useState, useEffect, useRef } from 'react'
import { suggestPlaces } from '../services/api'

function PlaceInput({
  id,
  label,
  placeholder,
  value,
  onChange,
  onSelect,
  selectedPlace,
  disabled = false,
}) {
  const [suggestions, setSuggestions] = useState([])
  const [open, setOpen] = useState(false)
  const [suggestLoading, setSuggestLoading] = useState(false)
  const wrapperRef = useRef(null)

  useEffect(() => {
    if (!value || value.length < 2 || disabled) {
      setSuggestions([])
      return undefined
    }

    const timer = setTimeout(() => {
      setSuggestLoading(true)
      suggestPlaces(value)
        .then((items) => {
          setSuggestions(items)
          setOpen(items.length > 0)
        })
        .catch(() => setSuggestions([]))
        .finally(() => setSuggestLoading(false))
    }, 350)

    return () => clearTimeout(timer)
  }, [value, disabled])

  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (place) => {
    onChange(place.label)
    onSelect(place)
    setOpen(false)
    setSuggestions([])
  }

  const handleInputChange = (e) => {
    onChange(e.target.value)
    onSelect(null)
  }

  return (
    <div className="form-group place-input-wrap" ref={wrapperRef}>
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={handleInputChange}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        disabled={disabled}
        autoComplete="off"
        required
      />
      {suggestLoading && (
        <span className="place-input-hint">Suggestions loading...</span>
      )}
      {selectedPlace && !disabled && (
        <span className="place-resolved">
          Selected: {selectedPlace.short_name || selectedPlace.label}
        </span>
      )}
      {open && suggestions.length > 0 && (
        <ul className="place-suggestions" role="listbox" aria-label={`${label} suggestions`}>
          {suggestions.map((place) => (
            <li key={`${place.lat}-${place.lon}`}>
              <button
                type="button"
                className="place-suggestion-item"
                onClick={() => handleSelect(place)}
                role="option"
              >
                {place.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default PlaceInput

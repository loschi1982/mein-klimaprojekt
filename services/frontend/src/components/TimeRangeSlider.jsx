import { useRef, useCallback } from 'react'
import { MIN_YEAR, MAX_YEAR } from '../context/AppContext'

export default function TimeRangeSlider({ value, onChange }) {
  const [fromYear, toYear] = value
  const trackRef = useRef(null)

  const pct = useCallback(
    (year) => ((year - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100,
    []
  )

  function handleFrom(e) {
    const v = Math.min(Number(e.target.value), toYear - 1)
    onChange([v, toYear])
  }

  function handleTo(e) {
    const v = Math.max(Number(e.target.value), fromYear + 1)
    onChange([fromYear, v])
  }

  const leftPct = pct(fromYear)
  const rightPct = pct(toYear)

  return (
    <div className="time-slider">
      <div className="time-slider-labels">
        <span className="time-slider-year time-slider-year--from">{fromYear}</span>
        <span className="time-slider-title">Zeitraum</span>
        <span className="time-slider-year time-slider-year--to">{toYear}</span>
      </div>

      <div className="time-slider-track" ref={trackRef}>
        {/* Aktiver Bereich zwischen den Handles */}
        <div
          className="time-slider-range"
          style={{ left: `${leftPct}%`, width: `${rightPct - leftPct}%` }}
        />
        <input
          type="range"
          className="time-slider-input time-slider-input--from"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={fromYear}
          onChange={handleFrom}
          aria-label="Startjahr"
        />
        <input
          type="range"
          className="time-slider-input time-slider-input--to"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={toYear}
          onChange={handleTo}
          aria-label="Endjahr"
        />
      </div>

      <div className="time-slider-ticks">
        {[MIN_YEAR, 1920, 1950, 1980, 2000, MAX_YEAR].map(y => (
          <span key={y} style={{ left: `${pct(y)}%` }}>{y}</span>
        ))}
      </div>
    </div>
  )
}

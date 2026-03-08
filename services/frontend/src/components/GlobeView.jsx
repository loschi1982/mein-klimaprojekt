import { useEffect, useRef, useState, useCallback } from 'react'
import Globe from 'react-globe.gl'
import { fetchZonalTemperature, fetchCo2Annual } from '../api/client'

// Latitude bands corresponding to GISS zone names
const ZONE_BANDS = [
  { zone: '64N-90N', latMin: 64,  latMax: 90  },
  { zone: '44N-64N', latMin: 44,  latMax: 64  },
  { zone: '24N-44N', latMin: 24,  latMax: 44  },
  { zone: 'EQU-24N', latMin: 0,   latMax: 24  },
  { zone: '24S-EQU', latMin: -24, latMax: 0   },
  { zone: '44S-24S', latMin: -44, latMax: -24 },
  { zone: '64S-44S', latMin: -64, latMax: -44 },
  { zone: '90S-64S', latMin: -90, latMax: -64 },
]

function getZoneForLat(lat) {
  for (const b of ZONE_BANDS) {
    if (lat >= b.latMin && lat <= b.latMax) return b.zone
  }
  return null
}

// Color scale: blue (cold) → white (neutral) → red (warm)
function anomalyColor(value) {
  if (value === null || value === undefined) return 'rgba(128,128,128,0.3)'
  const v = Math.max(-2, Math.min(2, value))
  if (v >= 0) {
    const t = v / 2
    const r = Math.round(255)
    const g = Math.round(255 * (1 - t))
    const b = Math.round(255 * (1 - t))
    return `rgba(${r},${g},${b},0.75)`
  } else {
    const t = (-v) / 2
    const r = Math.round(255 * (1 - t))
    const g = Math.round(255 * (1 - t))
    const b = Math.round(255)
    return `rgba(${r},${g},${b},0.75)`
  }
}

const MIN_YEAR = 1880
const MAX_YEAR = new Date().getFullYear() - 1

export default function GlobeView() {
  const globeRef = useRef()
  const [year, setYear] = useState(2020)
  const [playing, setPlaying] = useState(false)
  const [zonalData, setZonalData] = useState([])   // all years
  const [co2Annual, setCo2Annual] = useState([])
  const [countries, setCountries] = useState({ features: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  // Load all data once
  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetchZonalTemperature(null),
      fetchCo2Annual(MIN_YEAR, MAX_YEAR),
      fetch('https://raw.githubusercontent.com/vasturiano/react-globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson')
        .then(r => r.json()),
    ])
      .then(([zonal, co2, geo]) => {
        setZonalData(zonal.data || [])
        setCo2Annual(co2.series || [])
        setCountries(geo)
        setLoading(false)
      })
      .catch(e => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

  // Year animation
  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setYear(y => {
          if (y >= MAX_YEAR) { setPlaying(false); return MAX_YEAR }
          return y + 1
        })
      }, 200)
    } else {
      clearInterval(intervalRef.current)
    }
    return () => clearInterval(intervalRef.current)
  }, [playing])

  // Build zonal map for current year
  const currentZones = {}
  const yearRow = zonalData.find(r => r.year === year)
  if (yearRow) {
    for (const zone of ZONE_BANDS) {
      currentZones[zone.zone] = yearRow[zone.zone] ?? null
    }
  }

  // CO₂ value for current year
  const co2Row = co2Annual.find(r => r.year === year)
  const co2Value = co2Row ? co2Row.value : null

  // Color countries by their latitude zone
  const getCountryColor = useCallback((feat) => {
    const lat = feat.properties?.LABEL_Y ?? feat.properties?.LAT ?? null
    if (lat === null) return 'rgba(128,128,128,0.3)'
    const zone = getZoneForLat(lat)
    if (!zone || currentZones[zone] === null) return 'rgba(128,128,128,0.3)'
    return anomalyColor(currentZones[zone])
  }, [year, zonalData]) // eslint-disable-line

  const getCountryLabel = useCallback((feat) => {
    const lat = feat.properties?.LABEL_Y ?? null
    const zone = lat !== null ? getZoneForLat(lat) : null
    const val = zone ? currentZones[zone] : null
    const anomaly = val !== null ? `${val > 0 ? '+' : ''}${val.toFixed(2)} °C` : 'k.A.'
    return `<div style="background:#1a1a2e;color:#fff;padding:6px 10px;border-radius:6px;font-size:12px">
      <b>${feat.properties?.NAME ?? ''}</b><br/>
      Zone: ${zone ?? '–'}<br/>
      Anomalie: ${anomaly}
    </div>`
  }, [year, zonalData]) // eslint-disable-line

  if (loading) return <div className="globe-loading">Globusdaten werden geladen…</div>
  if (error) return (
    <div className="globe-error">
      <p>Fehler beim Laden der Globusdaten: {error}</p>
      <p>Stelle sicher, dass <code>nasa_giss_zonal</code> und <code>esrl_mauna_loa</code> importiert wurden.</p>
    </div>
  )

  return (
    <div className="globe-view">
      <div className="globe-header">
        <h2>3D-Globus: Zonale Temperaturanomalien</h2>
        <p className="globe-subtitle">NASA GISS · Referenz 1951–1980 · Jahr: <strong>{year}</strong></p>
      </div>

      <div className="globe-controls">
        <button
          className="globe-btn"
          onClick={() => setPlaying(p => !p)}
          aria-label={playing ? 'Pause' : 'Abspielen'}
        >
          {playing ? '⏸ Pause' : '▶ Abspielen'}
        </button>
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          value={year}
          onChange={e => { setPlaying(false); setYear(Number(e.target.value)) }}
          className="globe-year-slider"
          aria-label="Jahr"
        />
        <span className="globe-year-label">{year}</span>
      </div>

      {co2Value !== null && (
        <div className="co2-overlay">
          <div className="co2-overlay-label">CO₂ Jahresmittel</div>
          <div className="co2-overlay-value">{co2Value.toFixed(1)} <span>ppm</span></div>
          <div className="co2-overlay-source">NOAA/ESRL Mauna Loa</div>
        </div>
      )}

      <div className="globe-legend">
        <span style={{ color: '#4444ff' }}>● kälter</span>
        <span style={{ color: '#aaa' }}>● normal</span>
        <span style={{ color: '#ff4444' }}>● wärmer</span>
      </div>

      <div className="globe-canvas">
        <Globe
          ref={globeRef}
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
          backgroundColor="#0d0d1a"
          polygonsData={countries.features}
          polygonCapColor={getCountryColor}
          polygonSideColor={() => 'rgba(0,0,0,0.15)'}
          polygonStrokeColor={() => '#333'}
          polygonLabel={getCountryLabel}
          polygonAltitude={0.005}
          width={800}
          height={520}
        />
      </div>

      <div className="globe-zones-table">
        <h3>Zonale Anomalien {year}</h3>
        <table>
          <thead>
            <tr><th>Zone</th><th>Anomalie (°C)</th></tr>
          </thead>
          <tbody>
            {ZONE_BANDS.map(({ zone }) => {
              const val = currentZones[zone]
              return (
                <tr key={zone}>
                  <td>{zone}</td>
                  <td style={{ color: val == null ? '#888' : val > 0 ? '#f66' : '#66f' }}>
                    {val != null ? `${val > 0 ? '+' : ''}${val.toFixed(2)}` : '–'}
                  </td>
                </tr>
              )
            })}
            {yearRow?.Glob !== null && yearRow?.Glob !== undefined && (
              <tr style={{ fontWeight: 'bold' }}>
                <td>Global</td>
                <td style={{ color: yearRow.Glob > 0 ? '#f66' : '#66f' }}>
                  {yearRow.Glob > 0 ? '+' : ''}{yearRow.Glob.toFixed(2)}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

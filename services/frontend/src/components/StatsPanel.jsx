import { useEffect, useState } from 'react'
import { fetchCo2Stats } from '../api/client'

function StatCard({ label, value, unit, highlight }) {
  return (
    <div className={`stat-card${highlight ? ' stat-card--highlight' : ''}`}>
      <div className="stat-value">
        {value !== null && value !== undefined ? value : '–'}
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  )
}

export default function StatsPanel() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchCo2Stats()
      .then(setStats)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="chart-loading">Lade Statistiken...</div>
  if (error) return <div className="chart-error"><p>Fehler: {error}</p></div>
  if (!stats) return null

  const slope = typeof stats.slope === 'number' ? stats.slope.toFixed(2) : '–'
  const mean = typeof stats.mean === 'number' ? stats.mean.toFixed(1) : '–'
  const maxVal = typeof stats.max_value === 'number' ? stats.max_value.toFixed(1) : '–'
  const minVal = typeof stats.min_value === 'number' ? stats.min_value.toFixed(1) : '–'
  const count = stats.count ?? '–'
  const anomalies = stats.anomaly_count ?? '–'
  const minDate = stats.min_date?.slice(0, 7) ?? '–'
  const maxDate = stats.max_date?.slice(0, 7) ?? '–'

  return (
    <div className="chart-container">
      <h2 className="chart-title">CO₂-Statistiken – Mauna Loa</h2>
      <p className="chart-subtitle">
        Analysezeitraum: {minDate} – {maxDate} · {count} Messpunkte
      </p>
      <div className="stats-grid">
        <StatCard label="Aktueller Maximalwert" value={maxVal} unit=" ppm" highlight />
        <StatCard label="Minimaler Wert" value={minVal} unit=" ppm" />
        <StatCard label="Mittelwert" value={mean} unit=" ppm" />
        <StatCard label="Jährl. Anstieg (Trend)" value={slope} unit=" ppm/Jahr" highlight />
        <StatCard label="Messpunkte gesamt" value={count} />
        <StatCard label="Erkannte Anomalien" value={anomalies} />
      </div>

      <div className="threshold-bar">
        <div className="threshold-item">
          <span className="threshold-dot" style={{ background: '#f59e0b' }} />
          <span>280 ppm – Vorindustriell</span>
        </div>
        <div className="threshold-item">
          <span className="threshold-dot" style={{ background: '#ef4444' }} />
          <span>350 ppm – Sicherheitsgrenze (Hansen 1988)</span>
        </div>
        <div className="threshold-item">
          <span className="threshold-dot" style={{ background: '#a78bfa' }} />
          <span>420+ ppm – Aktuelles Niveau</span>
        </div>
      </div>
    </div>
  )
}

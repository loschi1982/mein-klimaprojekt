import { useEffect, useState } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import { fetchAnomalies } from '../api/client'

const SEVERITY_COLORS = {
  critical: '#ef4444',
  warning: '#f59e0b',
  info: '#60a5fa',
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{d.date}</p>
      <p style={{ color: '#e2e8f0', margin: '2px 0', fontSize: 13 }}>
        CO₂: {d.value?.toFixed(2)} ppm
      </p>
      <p style={{ color: '#94a3b8', margin: '2px 0', fontSize: 12 }}>
        Z-Score: {d.z_score?.toFixed(2)}
      </p>
      <p style={{ color: SEVERITY_COLORS[d.severity] ?? '#94a3b8', margin: '2px 0', fontSize: 12 }}>
        Schwere: {d.severity}
      </p>
    </div>
  )
}

export default function AnomalyChart({ threshold = 2.0 }) {
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchAnomalies(threshold)
      .then(data => {
        const list = Array.isArray(data.anomalies) ? data.anomalies : []
        // Numerisches Jahr für X-Achse
        const mapped = list.map(a => ({
          ...a,
          yearNum: parseInt(a.date?.slice(0, 4) ?? '0', 10),
        }))
        setAnomalies(mapped)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [threshold])

  if (loading) return <div className="chart-loading">Lade Anomaliedaten...</div>
  if (error) return <div className="chart-error"><p>Fehler: {error}</p></div>

  return (
    <div className="chart-container">
      <h2 className="chart-title">CO₂-Anomalien (Z-Score ≥ {threshold})</h2>
      <p className="chart-subtitle">
        {anomalies.length} statistische Ausreißer gefunden · Methode: Z-Score
      </p>

      {anomalies.length === 0 ? (
        <div className="chart-empty">
          Keine Anomalien mit Z-Score ≥ {threshold} gefunden oder noch keine Daten importiert.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="yearNum"
              type="number"
              domain={['auto', 'auto']}
              stroke="#475569"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={false}
              name="Jahr"
            />
            <YAxis
              dataKey="value"
              type="number"
              domain={['auto', 'auto']}
              stroke="#475569"
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              tickLine={false}
              unit=" ppm"
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={350} stroke="#f59e0b" strokeDasharray="4 4" />
            <Scatter data={anomalies} name="Anomalien">
              {anomalies.map((a, i) => (
                <Cell
                  key={i}
                  fill={SEVERITY_COLORS[a.severity] ?? '#94a3b8'}
                  opacity={0.85}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      )}

      <div className="threshold-bar">
        {Object.entries(SEVERITY_COLORS).map(([sev, color]) => (
          <div key={sev} className="threshold-item">
            <span className="threshold-dot" style={{ background: color }} />
            <span>{sev}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { compareScenarios } from '../api/client'

const SCENARIO_COLORS = {
  rcp26: '#34d399',
  rcp45: '#60a5fa',
  rcp60: '#f59e0b',
  rcp85: '#ef4444',
}

const SCENARIO_LABELS = {
  rcp26: 'RCP 2.6',
  rcp45: 'RCP 4.5',
  rcp60: 'RCP 6.0',
  rcp85: 'RCP 8.5',
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      {payload.map(p => (
        <p key={p.dataKey} style={{ color: p.color, margin: '2px 0', fontSize: 13 }}>
          {SCENARIO_LABELS[p.dataKey] ?? p.dataKey}: {p.value?.toFixed(1)} ppm
        </p>
      ))}
    </div>
  )
}

export default function SimulationChart({ years = 50 }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    compareScenarios(years)
      .then(comparison => {
        // Merge alle Szenarien in eine flache Datenreihe nach Jahr
        const byYear = {}
        Object.entries(comparison).forEach(([scenarioId, result]) => {
          result.projection?.forEach(dp => {
            if (!byYear[dp.year]) byYear[dp.year] = { year: dp.year }
            byYear[dp.year][scenarioId] = dp.co2_ppm
          })
        })
        setData(Object.values(byYear).sort((a, b) => a.year - b.year))
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [years])

  if (loading) return <div className="chart-loading">Lade Simulationsdaten...</div>
  if (error) return <div className="chart-error"><p>Fehler: {error}</p></div>

  return (
    <div className="chart-container">
      <h2 className="chart-title">RCP-Szenario-Vergleich – CO₂-Projektion</h2>
      <p className="chart-subtitle">
        Vergleich aller RCP-Szenarien · Startjahr 2026 · Zeitraum: {years} Jahre
      </p>
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="year"
            stroke="#475569"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickLine={false}
          />
          <YAxis
            domain={['auto', 'auto']}
            stroke="#475569"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickLine={false}
            unit=" ppm"
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: 16, fontSize: 13 }}
            formatter={(value) => (
              <span style={{ color: '#94a3b8' }}>{SCENARIO_LABELS[value] ?? value}</span>
            )}
          />
          <ReferenceLine
            y={450}
            stroke="#f59e0b"
            strokeDasharray="4 4"
            label={{ value: '450 ppm', fill: '#f59e0b', fontSize: 11 }}
          />
          {Object.keys(SCENARIO_COLORS).map(id => (
            <Line
              key={id}
              type="monotone"
              dataKey={id}
              stroke={SCENARIO_COLORS[id]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      <div className="scenario-legend">
        {Object.entries(SCENARIO_LABELS).map(([id, label]) => (
          <div key={id} className="scenario-badge" style={{ borderColor: SCENARIO_COLORS[id] }}>
            <span className="scenario-dot" style={{ background: SCENARIO_COLORS[id] }} />
            <span style={{ color: '#cbd5e1', fontSize: 12 }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

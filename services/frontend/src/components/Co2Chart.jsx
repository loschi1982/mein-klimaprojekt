import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { fetchCo2Data } from '../api/client'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, padding: '8px 12px' }}>
      <p style={{ color: '#94a3b8', margin: 0, fontSize: 12 }}>{label}</p>
      <p style={{ color: '#34d399', margin: 0, fontWeight: 700 }}>
        {payload[0].value.toFixed(2)} ppm
      </p>
    </div>
  )
}

export default function Co2Chart() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchCo2Data('1960-01-01', '2024-12-31')
      .then(series => {
        // Jährliche Mittelwerte berechnen für übersichtlicheren Chart
        const byYear = {}
        series.forEach(({ date, value }) => {
          const year = date.slice(0, 4)
          if (!byYear[year]) byYear[year] = []
          byYear[year].push(value)
        })
        const annual = Object.entries(byYear).map(([year, vals]) => ({
          date: year,
          value: parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2)),
        }))
        setData(annual)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="chart-loading">Lade CO₂-Daten...</div>
  if (error) return (
    <div className="chart-error">
      <p>Fehler: {error}</p>
      <p style={{ fontSize: 13, color: '#94a3b8' }}>
        Stelle sicher, dass das Backend läuft und CO₂-Daten importiert wurden:<br />
        <code>POST http://localhost:8001/api/v1/ingest</code> mit <code>{`{"source":"esrl_mauna_loa"}`}</code>
      </p>
    </div>
  )

  return (
    <div className="chart-container">
      <h2 className="chart-title">CO₂-Konzentration (Mauna Loa, jährlich)</h2>
      <p className="chart-subtitle">Quelle: NOAA ESRL / Mauna Loa Observatory · Einheit: ppm</p>
      <ResponsiveContainer width="100%" height={380}>
        <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="date"
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
          <ReferenceLine y={350} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: '350 ppm (Sicherheitsgrenze)', fill: '#f59e0b', fontSize: 11 }} />
          <ReferenceLine y={400} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '400 ppm', fill: '#ef4444', fontSize: 11 }} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#34d399"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: '#34d399' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

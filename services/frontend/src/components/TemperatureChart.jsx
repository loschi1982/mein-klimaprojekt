import { useEffect, useState } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { fetchTemperature } from '../api/client'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const v = payload[0].value
  const color = v >= 0 ? '#ef4444' : '#60a5fa'
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label?.slice(0, 7)}</p>
      <p style={{ color, margin: '2px 0', fontWeight: 700, fontSize: 14 }}>
        {v >= 0 ? '+' : ''}{v?.toFixed(2)} °C
      </p>
      <p style={{ color: '#64748b', fontSize: 11 }}>Anomalie vs. 1951–1980</p>
    </div>
  )
}

export default function TemperatureChart({ fromYear, toYear, sourceUrl }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    const from = `${fromYear}-01-01`
    const to = `${toYear}-12-31`
    fetchTemperature(from, to)
      .then(result => {
        // Jährliche Mittelwerte berechnen
        const byYear = {}
        result.series.forEach(({ date, value }) => {
          const year = date.slice(0, 4)
          if (!byYear[year]) byYear[year] = []
          byYear[year].push(value)
        })
        const annual = Object.entries(byYear).map(([year, vals]) => ({
          date: year,
          value: parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(3)),
        }))
        setData(annual)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [fromYear, toYear])

  if (loading) return <div className="chart-loading">Lade Temperaturdaten…</div>
  if (error) return (
    <div className="chart-error">
      <p>Fehler: {error}</p>
      <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
        Bitte zuerst im Admin-Bereich "NASA GISS – Globale Temperaturanomalie" importieren.
      </p>
    </div>
  )

  const lastVal = data[data.length - 1]?.value
  const lastYear = data[data.length - 1]?.date

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div>
          <h2 className="chart-title">Globale Temperaturanomalie (NASA GISS)</h2>
          <p className="chart-subtitle">
            Jährliche Mittelwerte · Referenzperiode 1951–1980 · Quelle:{' '}
            <a href={sourceUrl || 'https://data.giss.nasa.gov/gistemp/'} target="_blank" rel="noreferrer" className="source-link">
              NASA GISS Surface Temperature Analysis (GISTEMP v4)
            </a>
          </p>
        </div>
        {lastVal !== undefined && (
          <div className="chart-current-value">
            <span style={{ color: lastVal >= 0 ? '#ef4444' : '#60a5fa', fontSize: '2rem', fontWeight: 700 }}>
              {lastVal >= 0 ? '+' : ''}{lastVal.toFixed(2)}°C
            </span>
            <span className="chart-current-label">{lastYear}</span>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={380}>
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="tempGradientPos" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="tempGradientNeg" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
            </linearGradient>
          </defs>
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
            tickFormatter={v => `${v >= 0 ? '+' : ''}${v}°C`}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="#475569" strokeWidth={1} />
          <ReferenceLine
            y={1.5}
            stroke="#f59e0b"
            strokeDasharray="4 4"
            label={{ value: '+1.5°C (Paris-Ziel)', fill: '#f59e0b', fontSize: 11 }}
          />
          <ReferenceLine
            y={2.0}
            stroke="#ef4444"
            strokeDasharray="4 4"
            label={{ value: '+2.0°C', fill: '#ef4444', fontSize: 11 }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#ef4444"
            strokeWidth={2}
            fill="url(#tempGradientPos)"
            dot={false}
            activeDot={{ r: 4 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

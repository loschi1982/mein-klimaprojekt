import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { fetchSeries } from '../api/client'

const SOURCE_ID = 'csiro_sea_level'
const SOURCE_URL = 'https://www.cmar.csiro.au/sealevel/'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      <p style={{ color: '#38bdf8', margin: '2px 0', fontWeight: 700 }}>
        {payload[0].value?.toFixed(1)} mm
      </p>
    </div>
  )
}

export default function SeaLevelChart({ fromYear, toYear }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    const from = `${fromYear}-01-01`
    const to = `${toYear}-12-31`
    fetchSeries(SOURCE_ID, from, to)
      .then(result => {
        // Jährliche Mittelwerte
        const byYear = {}
        result.series.forEach(({ date, value }) => {
          const year = date.slice(0, 4)
          if (!byYear[year]) byYear[year] = []
          byYear[year].push(value)
        })
        const annual = Object.entries(byYear).map(([year, vals]) => ({
          date: year,
          value: parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)),
        }))
        setData(annual)
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [fromYear, toYear])

  if (loading) return <div className="chart-loading">Lade Meeresspiegel-Daten…</div>
  if (error) return (
    <div className="chart-error">
      <p>Fehler: {error}</p>
      <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
        Bitte zuerst im Admin-Bereich <code>csiro_sea_level</code> importieren.
      </p>
    </div>
  )

  const lastVal = data[data.length - 1]?.value
  const firstVal = data[0]?.value
  const rise = lastVal !== undefined && firstVal !== undefined
    ? (lastVal - firstVal).toFixed(0)
    : null

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div>
          <h2 className="chart-title">Globaler Meeresspiegel – CSIRO Rekonstruktion</h2>
          <p className="chart-subtitle">
            Jährliche Mittelwerte · Einheit: mm · Referenz: 1990 · Quelle:{' '}
            <a href={SOURCE_URL} target="_blank" rel="noreferrer" className="source-link">
              CSIRO (Church &amp; White 2011)
            </a>
          </p>
        </div>
        <div className="sealevel-stats">
          {lastVal !== undefined && (
            <div className="chart-current-value">
              <span style={{ color: '#38bdf8', fontSize: '2rem', fontWeight: 700 }}>
                {lastVal > 0 ? '+' : ''}{lastVal.toFixed(0)}
              </span>
              <span className="chart-current-label">mm · {data[data.length - 1]?.date}</span>
            </div>
          )}
          {rise !== null && (
            <div className="sealevel-rise-badge">
              ↑ {rise} mm Anstieg im Zeitraum
            </div>
          )}
        </div>
      </div>

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
            unit=" mm"
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="#475569" strokeDasharray="4 4" />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: '#38bdf8' }}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="sealevel-note">
        Positive Werte = Meeresspiegel über dem 1990er-Mittel. Daten: CSIRO Church &amp; White 2011,
        rekonstruierte Tide-Gauge-Messungen 1880–2015.
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { fetchSeries } from '../api/client'

const SOURCE_META = {
  esrl_mauna_loa: {
    title: 'CO₂-Konzentration – Mauna Loa Observatory',
    color: '#34d399',
    sourceLabel: 'NOAA GML / Mauna Loa Observatory',
    sourceUrl: 'https://gml.noaa.gov/ccgg/trends/',
    refLines: [
      { y: 350, color: '#f59e0b', label: '350 ppm (Sicherheitsgrenze)' },
      { y: 400, color: '#ef4444', label: '400 ppm' },
    ],
  },
  esrl_co2_global: {
    title: 'CO₂-Konzentration – Globaler Mittelwert',
    color: '#60a5fa',
    sourceLabel: 'NOAA GML – Marine Surface CO₂',
    sourceUrl: 'https://gml.noaa.gov/ccgg/trends/gl_data.html',
    refLines: [
      { y: 350, color: '#f59e0b', label: '350 ppm' },
      { y: 400, color: '#ef4444', label: '400 ppm' },
    ],
  },
  esrl_ch4: {
    title: 'Methan (CH₄) – Globaler Mittelwert',
    color: '#a78bfa',
    sourceLabel: 'NOAA GML – Global CH₄',
    sourceUrl: 'https://gml.noaa.gov/ccgg/trends_ch4/',
    refLines: [
      { y: 1800, color: '#f59e0b', label: '1800 ppb' },
    ],
  },
}

const CustomTooltip = ({ active, payload, label, unit, color }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <p className="tooltip-label">{label}</p>
      <p style={{ color, margin: '2px 0', fontWeight: 700 }}>
        {payload[0].value?.toFixed(2)} {unit}
      </p>
    </div>
  )
}

export default function ClimateSeriesChart({ sourceId, fromYear, toYear }) {
  const [data, setData] = useState([])
  const [meta, setMeta] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const cfg = SOURCE_META[sourceId] ?? {
    title: sourceId,
    color: '#34d399',
    sourceLabel: '',
    sourceUrl: '#',
    refLines: [],
  }

  useEffect(() => {
    setLoading(true)
    setError(null)
    const from = `${fromYear}-01-01`
    const to = `${toYear}-12-31`
    fetchSeries(sourceId, from, to)
      .then(result => {
        setMeta(result)
        // Jährliche Mittelwerte
        const byYear = {}
        result.series.forEach(({ date, value }) => {
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
  }, [sourceId, fromYear, toYear])

  if (loading) return <div className="chart-loading">Lade Daten…</div>
  if (error) return (
    <div className="chart-error">
      <p>Fehler: {error}</p>
      <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
        Bitte zuerst im Admin-Bereich importieren.
      </p>
    </div>
  )

  const unit = meta?.unit ?? ''
  const lastVal = data[data.length - 1]?.value
  const lastYear = data[data.length - 1]?.date

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div>
          <h2 className="chart-title">{cfg.title}</h2>
          <p className="chart-subtitle">
            Jährliche Mittelwerte · Einheit: {unit} · Quelle:{' '}
            <a href={cfg.sourceUrl} target="_blank" rel="noreferrer" className="source-link">
              {cfg.sourceLabel}
            </a>
          </p>
        </div>
        {lastVal !== undefined && (
          <div className="chart-current-value">
            <span style={{ color: cfg.color, fontSize: '2rem', fontWeight: 700 }}>
              {lastVal.toFixed(1)}
            </span>
            <span className="chart-current-label">{unit} · {lastYear}</span>
          </div>
        )}
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
            unit={` ${unit}`}
          />
          <Tooltip content={<CustomTooltip unit={unit} color={cfg.color} />} />
          {cfg.refLines.map(ref => (
            <ReferenceLine
              key={ref.y}
              y={ref.y}
              stroke={ref.color}
              strokeDasharray="4 4"
              label={{ value: ref.label, fill: ref.color, fontSize: 11 }}
            />
          ))}
          <Line
            type="monotone"
            dataKey="value"
            stroke={cfg.color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 5, fill: cfg.color }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

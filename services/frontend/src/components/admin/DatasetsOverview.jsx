import { useEffect, useState } from 'react'
import { fetchDatasets } from '../../api/client'

export default function DatasetsOverview() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  function load() {
    setLoading(true)
    fetchDatasets()
      .then(setDatasets)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <div className="admin-loading">Lade Datensätze…</div>
  if (error) return <div className="admin-error">Fehler: {error}</div>

  return (
    <div className="admin-section">
      <div className="admin-section-header">
        <h3 className="admin-section-title">Importierte Datensätze</h3>
        <button className="btn btn--secondary" onClick={load}>↻ Aktualisieren</button>
      </div>

      {datasets.length === 0 ? (
        <div className="admin-empty">
          Noch keine Datensätze importiert. Nutze "Datenquellen" oben, um Daten zu laden.
        </div>
      ) : (
        <table className="admin-table">
          <thead>
            <tr>
              <th>Dateiname</th>
              <th>Zeilen</th>
              <th>Spalten</th>
              <th>Zeitraum</th>
            </tr>
          </thead>
          <tbody>
            {datasets.map(ds => (
              <tr key={ds.name}>
                <td className="td-name">{ds.name}</td>
                <td>{ds.rows?.toLocaleString('de-DE') ?? '–'}</td>
                <td>{Array.isArray(ds.columns) ? ds.columns.join(', ') : '–'}</td>
                <td>
                  {ds.date_range
                    ? `${ds.date_range.min ?? '?'} – ${ds.date_range.max ?? '?'}`
                    : '–'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

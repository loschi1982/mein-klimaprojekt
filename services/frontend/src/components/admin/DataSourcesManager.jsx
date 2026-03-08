import { useEffect, useState } from 'react'
import { fetchSources, ingestSource } from '../../api/client'

const STATUS_LABEL = {
  idle: '',
  loading: 'Importiere…',
  success: 'Erfolgreich importiert',
  error: 'Fehler beim Import',
}

export default function DataSourcesManager() {
  const [sources, setSources] = useState([])
  const [status, setStatus] = useState({}) // { [sourceId]: 'idle'|'loading'|'success'|'error' }
  const [messages, setMessages] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSources()
      .then(setSources)
      .catch(() => setSources([]))
      .finally(() => setLoading(false))
  }, [])

  async function handleImport(sourceId) {
    setStatus(s => ({ ...s, [sourceId]: 'loading' }))
    setMessages(m => ({ ...m, [sourceId]: '' }))
    try {
      const result = await ingestSource(sourceId)
      setStatus(s => ({ ...s, [sourceId]: 'success' }))
      setMessages(m => ({ ...m, [sourceId]: result.file ?? 'OK' }))
    } catch (err) {
      setStatus(s => ({ ...s, [sourceId]: 'error' }))
      setMessages(m => ({ ...m, [sourceId]: err.message }))
    }
  }

  if (loading) return <div className="admin-loading">Lade Datenquellen…</div>

  return (
    <div className="admin-section">
      <h3 className="admin-section-title">Datenquellen</h3>
      <p className="admin-section-desc">
        Importiere Klimadaten aus NOAA ESRL-Quellen ins lokale Datensystem.
      </p>
      <div className="source-list">
        {sources.map(src => {
          const st = status[src.id] ?? 'idle'
          return (
            <div key={src.id} className="source-card">
              <div className="source-info">
                <div className="source-name">{src.name}</div>
                <div className="source-desc">{src.description}</div>
                <div className="source-meta">
                  <span className="badge">{src.format?.toUpperCase()}</span>
                  <span className="badge">{src.unit}</span>
                </div>
              </div>
              <div className="source-action">
                {st === 'success' && (
                  <span className="status-tag status-tag--success">✓ {messages[src.id]}</span>
                )}
                {st === 'error' && (
                  <span className="status-tag status-tag--error">✗ {messages[src.id]}</span>
                )}
                <button
                  className={`btn btn--primary${st === 'loading' ? ' btn--loading' : ''}`}
                  onClick={() => handleImport(src.id)}
                  disabled={st === 'loading'}
                >
                  {st === 'loading' ? 'Importiere…' : 'Importieren'}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { fetchPublishedReports } from '../api/client'
import { useAppContext } from '../context/AppContext'

export default function ReportsPage() {
  const { setCurrentView } = useAppContext()
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchPublishedReports()
      .then(data => setReports(data.reports || []))
      .catch(() => setError('Berichte konnten nicht geladen werden.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="reports-page">
        <p className="reports-loading">Lade Berichte…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="reports-page">
        <p className="reports-error-msg">{error}</p>
      </div>
    )
  }

  return (
    <div className="reports-page">
      <div className="reports-page-header">
        <h2 className="reports-page-title">Klimaberichte</h2>
        <p className="reports-page-desc">
          KI-gestützte Auswertungen wissenschaftlicher Fachliteratur zum Klimawandel
        </p>
      </div>

      {reports.length === 0 ? (
        <p className="reports-empty-public">Noch keine Berichte veröffentlicht.</p>
      ) : (
        <div className="reports-grid">
          {reports.map(r => (
            <button
              key={r.id}
              className="report-card"
              onClick={() => setCurrentView({ id: 'report_detail', reportId: r.id })}
            >
              <div className="report-card-date">
                {new Date(r.updated_at).toLocaleDateString('de-DE', {
                  day: '2-digit', month: 'long', year: 'numeric',
                })}
              </div>
              <div className="report-card-title">{r.title}</div>
              {r.tags.length > 0 && (
                <div className="report-card-tags">
                  {r.tags.map(t => <span key={t} className="report-card-tag">{t}</span>)}
                </div>
              )}
              <div className="report-card-arrow">Bericht lesen →</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

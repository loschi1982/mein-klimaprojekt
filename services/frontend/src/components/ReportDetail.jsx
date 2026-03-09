import { useState, useEffect } from 'react'
import { fetchPublishedReport } from '../api/client'
import { useAppContext } from '../context/AppContext'

export default function ReportDetail({ reportId }) {
  const { setCurrentView } = useAppContext()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchPublishedReport(reportId)
      .then(setReport)
      .catch(() => setError('Bericht konnte nicht geladen werden.'))
      .finally(() => setLoading(false))
  }, [reportId])

  function goBack() {
    setCurrentView({ id: 'reports' })
  }

  if (loading) {
    return (
      <div className="report-detail">
        <button className="report-back-btn" onClick={goBack}>← Alle Berichte</button>
        <p className="reports-loading">Lade Bericht…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="report-detail">
        <button className="report-back-btn" onClick={goBack}>← Alle Berichte</button>
        <p className="reports-error-msg">{error}</p>
      </div>
    )
  }

  return (
    <div className="report-detail">
      <button className="report-back-btn" onClick={goBack}>← Alle Berichte</button>

      <h2 className="report-detail-title">{report.title}</h2>

      <div className="report-detail-meta">
        <span>
          {new Date(report.updated_at).toLocaleDateString('de-DE', {
            day: '2-digit', month: 'long', year: 'numeric',
          })}
        </span>
        {report.tags?.length > 0 && (
          <span className="report-detail-tags">
            {report.tags.map(t => <span key={t} className="report-card-tag">{t}</span>)}
          </span>
        )}
      </div>

      <div
        className="report-detail-content"
        dangerouslySetInnerHTML={{ __html: report.content }}
      />
    </div>
  )
}

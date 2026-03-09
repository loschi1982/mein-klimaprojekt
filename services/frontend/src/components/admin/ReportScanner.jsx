import { useState, useEffect } from 'react'
import { fetchScanTopics, scanReports, saveReport } from '../../api/client'

function PaperCard({ paper, index }) {
  return (
    <div className="scan-paper-card">
      <div className="scan-paper-num">[Artikel {index}]</div>
      <div className="scan-paper-body">
        <div className="scan-paper-title">
          {paper.url
            ? <a href={paper.url} target="_blank" rel="noreferrer">{paper.title}</a>
            : paper.title}
          {paper.year && <span className="scan-paper-year"> ({paper.year})</span>}
        </div>
        {paper.authors?.length > 0 && (
          <div className="scan-paper-authors">
            <strong>Hauptautoren:</strong>{' '}
            {paper.authors.slice(0, 4).join(', ')}
            {paper.authors.length > 4 && ' et al.'}
          </div>
        )}
        {paper.doi && (
          <div className="scan-paper-doi">
            <strong>DOI:</strong>{' '}
            <a href={paper.doi} target="_blank" rel="noreferrer">{paper.doi}</a>
          </div>
        )}
        {paper.abstract_snippet && (
          <div className="scan-paper-abstract">{paper.abstract_snippet}</div>
        )}
      </div>
    </div>
  )
}

function SummaryText({ text }) {
  // Konvertiert einfaches Markdown zu HTML
  const html = text
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>')
  return (
    <div
      className="scan-summary-text"
      dangerouslySetInnerHTML={{ __html: `<p>${html}</p>` }}
    />
  )
}

export default function ReportScanner() {
  const [topics, setTopics] = useState([])
  const [selectedTopic, setSelectedTopic] = useState('')
  const [customTopic, setCustomTopic] = useState('')
  const [maxPapers, setMaxPapers] = useState(5)
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [saveStatus, setSaveStatus] = useState(null)

  useEffect(() => {
    fetchScanTopics()
      .then(t => {
        setTopics(t)
        setSelectedTopic(t[0]?.query ?? '')
      })
      .catch(() => {})
  }, [])

  const activeTopic = selectedTopic === '__custom__' ? customTopic : selectedTopic

  async function handleScan() {
    if (!activeTopic.trim()) return
    setScanning(true)
    setError(null)
    setResult(null)
    setSaveStatus(null)
    try {
      const data = await scanReports(activeTopic.trim(), maxPapers)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail?.message ?? e.message ?? 'Fehler beim Scannen')
    } finally {
      setScanning(false)
    }
  }

  async function handleSave() {
    if (!result) return
    setSaveStatus('saving')
    const topicLabel = topics.find(t => t.query === selectedTopic)?.label ?? activeTopic
    const contentHtml = `<p><em>Gescannt: ${new Date(result.scanned_at).toLocaleDateString('de-DE')}</em></p>`
      + `<hr/>`
      + result.summary
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br/>')
    try {
      await saveReport(
        `Literatur-Scan: ${topicLabel}`,
        `<p>${contentHtml}</p>`,
        'nasa_giss_global',
        ['literatur-scan', 'klimaanomalien'],
      )
      setSaveStatus('saved')
    } catch {
      setSaveStatus('error')
    }
  }

  return (
    <div className="admin-section">
      <h3 className="admin-section-title">Wissenschaftliche Literatur scannen</h3>
      <p className="admin-section-desc">
        Durchsucht die OpenAlex-Literaturdatenbank nach aktuellen Fachartikeln und erstellt
        einen KI-Bericht in einfacher Sprache – ausschließlich basierend auf den gefundenen Abstracts.
      </p>

      {/* Themenauswahl */}
      <div className="scan-controls">
        <div className="scan-field">
          <label className="scan-label">Thema</label>
          <select
            className="scan-select"
            value={selectedTopic}
            onChange={e => setSelectedTopic(e.target.value)}
          >
            {topics.map(t => (
              <option key={t.query} value={t.query}>{t.label}</option>
            ))}
            <option value="__custom__">✏ Eigenes Thema eingeben…</option>
          </select>
        </div>

        {selectedTopic === '__custom__' && (
          <div className="scan-field">
            <label className="scan-label">Eigenes Thema (Englisch empfohlen)</label>
            <input
              className="scan-input"
              type="text"
              value={customTopic}
              onChange={e => setCustomTopic(e.target.value)}
              placeholder="z.B. Arctic sea ice decline feedback mechanisms"
            />
          </div>
        )}

        <div className="scan-field scan-field--small">
          <label className="scan-label">Max. Artikel</label>
          <select
            className="scan-select"
            value={maxPapers}
            onChange={e => setMaxPapers(Number(e.target.value))}
          >
            {[3, 5, 7, 10].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>

        <button
          className={`btn btn--primary${scanning ? ' btn--loading' : ''}`}
          onClick={handleScan}
          disabled={scanning || !activeTopic.trim()}
        >
          {scanning ? '⏳ Scanne Literatur…' : '🔍 Scan starten'}
        </button>
      </div>

      {/* Fehler */}
      {error && (
        <div className="scan-error">
          <strong>Fehler:</strong> {error}
        </div>
      )}

      {/* Ergebnis */}
      {result && (
        <div className="scan-result">
          <div className="scan-result-header">
            <div>
              <h4 className="scan-result-title">KI-Bericht: {result.topic}</h4>
              <span className="scan-result-meta">
                {result.papers.length} Artikel · {' '}
                {new Date(result.scanned_at).toLocaleString('de-DE')} · {' '}
                {result.used_llm
                  ? <span className="badge-llm">✦ Claude KI</span>
                  : <span className="badge-rule">Regelbasiert</span>
                }
              </span>
            </div>
            <div className="scan-result-actions">
              <button
                className="btn btn--secondary"
                onClick={handleSave}
                disabled={saveStatus === 'saving' || saveStatus === 'saved'}
              >
                {saveStatus === 'saving' && '💾 Speichere…'}
                {saveStatus === 'saved' && '✓ Gespeichert'}
                {saveStatus === 'error' && '✗ Fehler'}
                {!saveStatus && '💾 Als Bericht speichern'}
              </button>
            </div>
          </div>

          {/* Quellenwarnung */}
          <div className="scan-source-notice">
            <span>ℹ</span>
            Alle Aussagen basieren ausschließlich auf den unten aufgeführten wissenschaftlichen Fachartikeln.
            Es wurden keine eigenen Informationen ergänzt.
          </div>

          {/* Zusammenfassung */}
          <div className="scan-summary">
            <SummaryText text={result.summary} />
          </div>

          {/* Verwendete Artikel */}
          <div className="scan-papers">
            <h4 className="scan-papers-title">Verwendete wissenschaftliche Artikel</h4>
            {result.papers.map((p, i) => (
              <PaperCard key={p.doi ?? p.title} paper={p} index={i + 1} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchScanTopics, scanReports, saveReport } from '../../api/client'

// ── Hilfsfunktionen ─────────────────────────────────────────────────────────

function parseHighlights(summary) {
  const match = summary.match(/## Auf einen Blick\n([\s\S]*?)(?=\n##|$)/)
  if (!match) return []
  return match[1]
    .split('\n')
    .filter(l => l.trim().startsWith('-'))
    .map(line => {
      const m = line.match(/^-\s*(.*?)\s*\*\*(.+?)\*\*\s*[–-]\s*(.+)$/)
      if (!m) return null
      return { prefix: m[1].trim(), value: m[2].trim(), label: m[3].trim() }
    })
    .filter(Boolean)
}

function stripHighlights(summary) {
  return summary.replace(/## Auf einen Blick\n[\s\S]*?(?=\n## )/, '')
}

function buildYearData(papers) {
  const counts = {}
  papers.forEach(p => {
    if (p.year) counts[p.year] = (counts[p.year] || 0) + 1
  })
  return Object.entries(counts)
    .sort(([a], [b]) => a - b)
    .map(([year, count]) => ({ year: String(year), count }))
}

// ── Teilkomponenten ──────────────────────────────────────────────────────────

function HighlightCards({ highlights }) {
  if (!highlights.length) return null
  return (
    <div className="scan-highlights">
      {highlights.map((h, i) => (
        <div key={i} className="scan-highlight-card">
          <div className="scan-highlight-prefix">{h.prefix}</div>
          <div className="scan-highlight-value">{h.value}</div>
          <div className="scan-highlight-label">{h.label}</div>
        </div>
      ))}
    </div>
  )
}

function YearChart({ papers }) {
  const data = buildYearData(papers)
  if (data.length < 2) return null
  return (
    <div className="scan-year-chart">
      <div className="scan-year-chart-title">Publikationsjahre der verwendeten Studien</div>
      <ResponsiveContainer width="100%" height={80}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: -28, bottom: 0 }}>
          <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#64748b' }} />
          <YAxis tick={{ fontSize: 10, fill: '#64748b' }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: '#0f172a', border: '1px solid #334155', fontSize: '0.75rem', color: '#e2e8f0' }}
            cursor={{ fill: 'rgba(59,130,246,0.1)' }}
          />
          <Bar dataKey="count" name="Artikel" fill="#3b82f6" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

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

// ── Hauptkomponente ──────────────────────────────────────────────────────────

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

  const highlights = result ? parseHighlights(result.summary) : []
  const summaryWithoutHighlights = result ? stripHighlights(result.summary) : ''

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

          {/* Auf einen Blick – Stat-Karten */}
          {highlights.length > 0 && <HighlightCards highlights={highlights} />}

          {/* Zusammenfassung */}
          <div className="scan-summary">
            <SummaryText text={summaryWithoutHighlights} />
          </div>

          {/* Publikationsjahr-Chart */}
          {result.papers.length >= 2 && <YearChart papers={result.papers} />}

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

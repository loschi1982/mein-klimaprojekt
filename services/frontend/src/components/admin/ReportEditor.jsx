import { useState, useRef, useEffect, useCallback } from 'react'
import { fetchAgentReport, fetchReports, saveReport, updateReport, deleteReport } from '../../api/client'

const SOURCE_OPTIONS = [
  { id: 'esrl_mauna_loa', label: 'CO₂ – Mauna Loa' },
  { id: 'esrl_co2_global', label: 'CO₂ – Global' },
  { id: 'esrl_ch4', label: 'Methan (CH₄)' },
  { id: 'nasa_giss_global', label: 'Temperatur – NASA GISS' },
]

function agentResultToHtml(data) {
  const { analyst, trend_detector } = data
  const lines = [
    '<h2>KI-Analysebericht – CO₂-Daten</h2>',
    `<h3>Zusammenfassung (Datenanalyst)</h3>`,
    `<p>${analyst.summary}</p>`,
    `<h3>Befunde</h3>`,
    `<ul>${analyst.findings.map(f => `<li>${f}</li>`).join('')}</ul>`,
    `<h3>Empfehlungen</h3>`,
    `<ul>${analyst.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>`,
    `<h3>Trendanalyse</h3>`,
    `<p>${trend_detector.summary}</p>`,
    `<ul>${trend_detector.findings.map(f => `<li>${f}</li>`).join('')}</ul>`,
  ]
  return lines.join('\n')
}

// ── WYSIWYG Toolbar ────────────────────────────────────────────────────────

function ToolbarBtn({ title, onClick, children }) {
  return (
    <button
      type="button"
      className="wysiwyg-btn"
      title={title}
      onMouseDown={e => { e.preventDefault(); onClick() }}
    >
      {children}
    </button>
  )
}

function WysiwygToolbar({ editorRef }) {
  const exec = (cmd, value = null) => {
    editorRef.current?.focus()
    document.execCommand(cmd, false, value)
  }

  return (
    <div className="wysiwyg-toolbar" role="toolbar" aria-label="Formatierungswerkzeuge">
      <ToolbarBtn title="Fett" onClick={() => exec('bold')}><b>B</b></ToolbarBtn>
      <ToolbarBtn title="Kursiv" onClick={() => exec('italic')}><i>I</i></ToolbarBtn>
      <ToolbarBtn title="Unterstrichen" onClick={() => exec('underline')}><u>U</u></ToolbarBtn>
      <span className="wysiwyg-sep" />
      <ToolbarBtn title="Überschrift 2" onClick={() => exec('formatBlock', 'h2')}>H2</ToolbarBtn>
      <ToolbarBtn title="Überschrift 3" onClick={() => exec('formatBlock', 'h3')}>H3</ToolbarBtn>
      <ToolbarBtn title="Absatz" onClick={() => exec('formatBlock', 'p')}>P</ToolbarBtn>
      <span className="wysiwyg-sep" />
      <ToolbarBtn title="Aufzählung" onClick={() => exec('insertUnorderedList')}>• Liste</ToolbarBtn>
      <ToolbarBtn title="Nummeriert" onClick={() => exec('insertOrderedList')}>1. Liste</ToolbarBtn>
      <span className="wysiwyg-sep" />
      <ToolbarBtn title="Alles löschen" onClick={() => { if (editorRef.current) editorRef.current.innerHTML = '' }}>✕ Leeren</ToolbarBtn>
    </div>
  )
}

// ── Berichte-Liste ─────────────────────────────────────────────────────────

function ReportsList({ reports, onEdit, onDelete, onRefresh }) {
  const [deleting, setDeleting] = useState(null)

  async function handleDelete(id) {
    setDeleting(id)
    try {
      await deleteReport(id)
      onRefresh()
    } finally {
      setDeleting(null)
    }
  }

  if (reports.length === 0) {
    return <p className="reports-empty">Noch keine Berichte gespeichert.</p>
  }

  return (
    <ul className="reports-list">
      {reports.map(r => (
        <li key={r.id} className="report-item">
          <div className="report-item-info">
            <span className="report-item-title">{r.title}</span>
            <span className="report-item-meta">
              {SOURCE_OPTIONS.find(s => s.id === r.source_id)?.label ?? r.source_id}
              {' · '}
              {new Date(r.updated_at).toLocaleDateString('de-DE')}
            </span>
            {r.tags.length > 0 && (
              <div className="report-item-tags">
                {r.tags.map(t => <span key={t} className="report-tag">{t}</span>)}
              </div>
            )}
          </div>
          <div className="report-item-actions">
            <button className="btn-sm btn-secondary" onClick={() => onEdit(r)}>Bearbeiten</button>
            <button
              className="btn-sm btn-danger"
              onClick={() => handleDelete(r.id)}
              disabled={deleting === r.id}
            >
              {deleting === r.id ? '…' : 'Löschen'}
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}

// ── Haupt-Komponente ───────────────────────────────────────────────────────

export default function ReportEditor() {
  const editorRef = useRef(null)
  const [title, setTitle] = useState('')
  const [sourceId, setSourceId] = useState('esrl_mauna_loa')
  const [tags, setTags] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [reports, setReports] = useState([])
  const [loadingReports, setLoadingReports] = useState(true)
  const [feedback, setFeedback] = useState(null)  // {type: 'success'|'error', msg}

  const showFeedback = (type, msg) => {
    setFeedback({ type, msg })
    setTimeout(() => setFeedback(null), 4000)
  }

  const loadReports = useCallback(async () => {
    setLoadingReports(true)
    try {
      const data = await fetchReports()
      setReports(data.reports || [])
    } catch {
      setReports([])
    } finally {
      setLoadingReports(false)
    }
  }, [])

  useEffect(() => { loadReports() }, [loadReports])

  async function handleGenerate() {
    setGenerating(true)
    setFeedback(null)
    try {
      const data = await fetchAgentReport()
      if (editorRef.current) {
        editorRef.current.innerHTML = agentResultToHtml(data)
      }
      if (!title) setTitle(`KI-Bericht CO₂ – ${new Date().toLocaleDateString('de-DE')}`)
      showFeedback('success', 'Bericht generiert. Jetzt bearbeiten und speichern.')
    } catch (e) {
      showFeedback('error', `Fehler: ${e.response?.data?.detail?.message ?? e.message}`)
    } finally {
      setGenerating(false)
    }
  }

  async function handleSave() {
    const content = editorRef.current?.innerHTML ?? ''
    if (!title.trim() || !content.trim()) {
      showFeedback('error', 'Bitte Titel und Inhalt angeben.')
      return
    }
    const tagList = tags.split(',').map(t => t.trim()).filter(Boolean)
    setSaving(true)
    try {
      if (editingId) {
        await updateReport(editingId, title, content, sourceId, tagList)
        showFeedback('success', 'Bericht aktualisiert.')
      } else {
        await saveReport(title, content, sourceId, tagList)
        showFeedback('success', 'Bericht gespeichert.')
      }
      await loadReports()
      handleNew()
    } catch (e) {
      showFeedback('error', `Fehler beim Speichern: ${e.message}`)
    } finally {
      setSaving(false)
    }
  }

  function handleEdit(report) {
    setEditingId(report.id)
    setTitle(report.title)
    setSourceId(report.source_id)
    setTags((report.tags ?? []).join(', '))
    // Load full content
    getReport(report.id).then(data => {
      if (editorRef.current) editorRef.current.innerHTML = data.content ?? ''
    }).catch(() => {})
  }

  function handleNew() {
    setEditingId(null)
    setTitle('')
    setSourceId('esrl_mauna_loa')
    setTags('')
    if (editorRef.current) editorRef.current.innerHTML = ''
  }

  // Import getReport for edit
  const [getReport] = useState(() => (id) => import('../../api/client').then(m => m.getReport(id)))

  return (
    <div className="report-editor">
      <div className="report-editor-header">
        <h2 className="admin-section-title">
          {editingId ? '✏️ Bericht bearbeiten' : '📝 Neuen Bericht erstellen'}
        </h2>
        {editingId && (
          <button className="btn-sm btn-secondary" onClick={handleNew}>+ Neuer Bericht</button>
        )}
      </div>

      {feedback && (
        <div className={`report-feedback report-feedback--${feedback.type}`}>
          {feedback.msg}
        </div>
      )}

      {/* Metadaten */}
      <div className="report-meta-row">
        <div className="form-group" style={{ flex: 2 }}>
          <label htmlFor="report-title">Titel</label>
          <input
            id="report-title"
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Berichtstitel…"
          />
        </div>
        <div className="form-group" style={{ flex: 1 }}>
          <label htmlFor="report-source">Datenquelle</label>
          <select
            id="report-source"
            value={sourceId}
            onChange={e => setSourceId(e.target.value)}
            className="report-select"
          >
            {SOURCE_OPTIONS.map(s => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
        </div>
        <div className="form-group" style={{ flex: 1 }}>
          <label htmlFor="report-tags">Tags (kommagetrennt)</label>
          <input
            id="report-tags"
            type="text"
            value={tags}
            onChange={e => setTags(e.target.value)}
            placeholder="co2, trend, 2024"
          />
        </div>
      </div>

      {/* Aktionsleiste oben */}
      <div className="report-actions-top">
        <button
          className="btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? '⏳ Generiere…' : '🤖 KI-Bericht generieren'}
        </button>
        <span className="report-hint">
          Generiert Analyse aus CO₂-Daten (esrl_mauna_loa muss importiert sein)
        </span>
      </div>

      {/* WYSIWYG Editor */}
      <div className="wysiwyg-wrapper">
        <WysiwygToolbar editorRef={editorRef} />
        <div
          ref={editorRef}
          className="wysiwyg-editor"
          contentEditable
          suppressContentEditableWarning
          data-placeholder="Bericht hier eingeben oder KI-Bericht generieren…"
          role="textbox"
          aria-label="Berichtseditor"
          aria-multiline="true"
        />
      </div>

      {/* Speichern */}
      <div className="report-actions-bottom">
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? '⏳ Speichern…' : (editingId ? '💾 Aktualisieren' : '💾 Bericht speichern')}
        </button>
        {editingId && (
          <button className="btn-sm btn-secondary" onClick={handleNew}>Abbrechen</button>
        )}
      </div>

      {/* Gespeicherte Berichte */}
      <div className="reports-section">
        <div className="reports-section-header">
          <h3 className="admin-section-title" style={{ fontSize: '1rem' }}>Gespeicherte Berichte</h3>
          <button className="btn-sm btn-secondary" onClick={loadReports} disabled={loadingReports}>
            {loadingReports ? '…' : '↺ Aktualisieren'}
          </button>
        </div>
        {loadingReports
          ? <p className="reports-empty">Lade…</p>
          : <ReportsList reports={reports} onEdit={handleEdit} onDelete={deleteReport} onRefresh={loadReports} />
        }
      </div>
    </div>
  )
}

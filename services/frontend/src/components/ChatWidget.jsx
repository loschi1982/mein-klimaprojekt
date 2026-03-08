import { useState, useRef, useEffect, useCallback } from 'react'
import { useAppContext } from '../context/AppContext'
import { sendChatMessage } from '../api/client'
import { NAV_ITEMS } from './NavBar'

// Ermittle Label des aktuellen Views aus NAV_ITEMS
function getViewLabel(viewId) {
  for (const item of NAV_ITEMS) {
    if (item.children) {
      const child = item.children.find(c => c.id === viewId)
      if (child) return child.label
    }
    if (item.id === viewId) return item.label
  }
  return viewId
}

// Ermittle sourceId des aktuellen Views
function getSourceId(viewId) {
  for (const item of NAV_ITEMS) {
    if (item.children) {
      const child = item.children.find(c => c.id === viewId)
      if (child?.sourceId) return child.sourceId
    }
  }
  return ''
}

const WELCOME = {
  role: 'assistant',
  content: 'Hallo! Ich bin dein Klimadaten-Assistent. Stelle mir Fragen zum aktuell angezeigten Datensatz oder zu allgemeinen Klimathemen.',
  id: 'welcome',
}

export default function ChatWidget() {
  const { currentView, timeRange } = useAppContext()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([
    'Was zeigt dieses Dashboard?',
    'Was ist der Treibhauseffekt?',
    'Was bedeutet Paris-Ziel?',
  ])
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  // Focus input when opened
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100)
  }, [open])

  const buildContext = useCallback(() => ({
    source_id: getSourceId(currentView.id),
    view_label: getViewLabel(currentView.id),
    from_year: timeRange[0],
    to_year: timeRange[1],
  }), [currentView, timeRange])

  async function handleSend(text) {
    const msg = (text ?? input).trim()
    if (!msg || loading) return
    setInput('')

    const userMsg = { role: 'user', content: msg, id: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    const history = messages
      .filter(m => m.role !== 'welcome' && m.id !== 'welcome')
      .slice(-8)
      .map(m => ({ role: m.role, content: m.content }))

    try {
      const data = await sendChatMessage(msg, buildContext(), history)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        used_llm: data.used_llm,
        id: Date.now() + 1,
      }])
      if (data.suggestions?.length) setSuggestions(data.suggestions)
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Verbindungsfehler – bitte Backend prüfen.',
        id: Date.now() + 1,
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleClear() {
    setMessages([WELCOME])
    setSuggestions([
      'Was zeigt dieses Dashboard?',
      'Was ist der Treibhauseffekt?',
      'Was bedeutet Paris-Ziel?',
    ])
  }

  const viewLabel = getViewLabel(currentView.id)

  return (
    <div className="chat-widget">
      {/* Toggle Button */}
      <button
        className={`chat-toggle${open ? ' chat-toggle--open' : ''}`}
        onClick={() => setOpen(o => !o)}
        aria-label={open ? 'Chat schließen' : 'Chat öffnen'}
        aria-expanded={open}
      >
        {open ? '✕' : '💬'}
      </button>

      {/* Chat Panel */}
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Klimadaten-Chat">
          {/* Header */}
          <div className="chat-header">
            <div>
              <span className="chat-title">Klimadaten-Assistent</span>
              <span className="chat-context-label">{viewLabel}</span>
            </div>
            <button className="chat-clear-btn" onClick={handleClear} title="Chat leeren">
              ↺
            </button>
          </div>

          {/* Messages */}
          <div className="chat-messages" role="log" aria-live="polite">
            {messages.map(msg => (
              <div key={msg.id} className={`chat-msg chat-msg--${msg.role}`}>
                <div className="chat-bubble">
                  {msg.content}
                  {msg.used_llm && (
                    <span className="chat-llm-badge" title="KI-generierte Antwort">✦</span>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-msg chat-msg--assistant">
                <div className="chat-bubble chat-bubble--typing">
                  <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && !loading && (
            <div className="chat-suggestions">
              {suggestions.map(s => (
                <button key={s} className="chat-suggestion-btn" onClick={() => handleSend(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="chat-input-row">
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              placeholder="Frage stellen…"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              aria-label="Chatnachricht eingeben"
            />
            <button
              className="chat-send-btn"
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              aria-label="Senden"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

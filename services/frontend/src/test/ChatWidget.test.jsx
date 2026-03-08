import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AppProvider } from '../context/AppContext'
import ChatWidget from '../components/ChatWidget'

window.HTMLElement.prototype.scrollIntoView = vi.fn()

vi.mock('../api/client', () => ({
  sendChatMessage: vi.fn().mockResolvedValue({
    answer: 'CO₂ steigt seit 1958 kontinuierlich an.',
    used_llm: false,
    suggestions: ['Was ist die 350-ppm-Grenze?', 'Wann wurde 400 ppm überschritten?'],
  }),
}))

function renderWidget() {
  return render(
    <AppProvider>
      <ChatWidget />
    </AppProvider>
  )
}

describe('ChatWidget', () => {
  beforeEach(() => vi.clearAllMocks())

  it('zeigt Chat-Toggle-Button', () => {
    renderWidget()
    expect(screen.getByRole('button', { name: /Chat öffnen/i })).toBeInTheDocument()
  })

  it('Chat-Panel ist initial geschlossen', () => {
    renderWidget()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('öffnet Chat-Panel beim Klick auf Toggle', async () => {
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument())
  })

  it('zeigt Willkommensnachricht nach Öffnen', async () => {
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() =>
      expect(screen.getAllByText(/Klimadaten-Assistent/i).length).toBeGreaterThan(0)
    )
  })

  it('zeigt Eingabefeld nach Öffnen', async () => {
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() =>
      expect(screen.getByRole('textbox', { name: /Chatnachricht/i })).toBeInTheDocument()
    )
  })

  it('zeigt Senden-Button', async () => {
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Senden/i })).toBeInTheDocument()
    )
  })

  it('zeigt Willkommensnachricht-Text', async () => {
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() =>
      expect(screen.getByText(/Klimadaten-Assistent.*Fragen/i)).toBeInTheDocument()
    )
  })

  it('sendet Nachricht und zeigt Antwort', async () => {
    const { sendChatMessage } = await import('../api/client')
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() => screen.getByRole('textbox'))

    const input = screen.getByRole('textbox', { name: /Chatnachricht/i })
    fireEvent.change(input, { target: { value: 'Was ist CO₂?' } })
    fireEvent.click(screen.getByRole('button', { name: /Senden/i }))

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalledWith(
      'Was ist CO₂?',
      expect.objectContaining({ source_id: expect.any(String) }),
      expect.any(Array),
    ))
    await waitFor(() =>
      expect(screen.getByText(/CO₂ steigt seit 1958/i)).toBeInTheDocument()
    )
  })

  it('zeigt Vorschläge nach Antwort', async () => {
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() => screen.getByRole('textbox'))

    const input = screen.getByRole('textbox', { name: /Chatnachricht/i })
    fireEvent.change(input, { target: { value: 'Hallo' } })
    fireEvent.click(screen.getByRole('button', { name: /Senden/i }))

    await waitFor(() =>
      expect(screen.getByText(/350-ppm-Grenze/i)).toBeInTheDocument()
    )
  })

  it('schließt Chat-Panel beim zweiten Klick', async () => {
    renderWidget()
    const toggle = screen.getByRole('button', { name: /Chat öffnen/i })
    fireEvent.click(toggle)
    await waitFor(() => screen.getByRole('dialog'))
    fireEvent.click(screen.getByRole('button', { name: /Chat schließen/i }))
    await waitFor(() =>
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    )
  })

  it('leert Chat beim Klick auf Leeren-Button', async () => {
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() => screen.getByRole('dialog'))
    // Sende eine Nachricht
    const input = screen.getByRole('textbox', { name: /Chatnachricht/i })
    fireEvent.change(input, { target: { value: 'Test' } })
    fireEvent.click(screen.getByRole('button', { name: /Senden/i }))
    await waitFor(() => screen.getByText(/CO₂ steigt/i))
    // Leeren
    fireEvent.click(screen.getByTitle(/Chat leeren/i))
    await waitFor(() =>
      expect(screen.queryByText(/CO₂ steigt/i)).not.toBeInTheDocument()
    )
  })

  it('Enter-Taste sendet Nachricht', async () => {
    const { sendChatMessage } = await import('../api/client')
    renderWidget()
    fireEvent.click(screen.getByRole('button', { name: /Chat öffnen/i }))
    await waitFor(() => screen.getByRole('textbox'))

    const input = screen.getByRole('textbox', { name: /Chatnachricht/i })
    fireEvent.change(input, { target: { value: 'Testfrage' } })
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })

    await waitFor(() => expect(sendChatMessage).toHaveBeenCalled())
  })
})

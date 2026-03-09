import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ReportScanner from '../components/admin/ReportScanner'

const MOCK_TOPICS = [
  { label: 'Arktische Verstärkung', query: 'arctic amplification' },
  { label: 'Nordhalbkugel Erwärmung', query: 'northern hemisphere warming' },
]

const MOCK_RESULT = {
  topic: 'arctic amplification',
  summary: '## Einleitung\n\nDie arktische Verstärkung [Artikel 1] beschreibt...\n\n**Quellen**\n1. Arctic Study (2022) – Jane Smith – [DOI](https://doi.org/10.1000/test)',
  used_llm: true,
  scanned_at: '2024-01-15T10:00:00Z',
  papers: [
    {
      title: 'Arctic Amplification Study',
      authors: ['Jane Smith', 'John Doe'],
      year: 2022,
      url: 'https://doi.org/10.1000/arctic',
      doi: 'https://doi.org/10.1000/arctic',
      abstract_snippet: 'This study examines Arctic amplification mechanisms…',
    },
  ],
}

vi.mock('../api/client', () => ({
  fetchScanTopics: vi.fn().mockResolvedValue([
    { label: 'Arktische Verstärkung', query: 'arctic amplification' },
    { label: 'Nordhalbkugel Erwärmung', query: 'northern hemisphere warming' },
  ]),
  scanReports: vi.fn().mockResolvedValue({
    topic: 'arctic amplification',
    summary: '## Einleitung\n\nDie arktische Verstärkung [Artikel 1] beschreibt...\n\n**Quellen**\n1. Arctic Study (2022) – Jane Smith – [DOI](https://doi.org/10.1000/test)',
    used_llm: true,
    scanned_at: '2024-01-15T10:00:00Z',
    papers: [
      {
        title: 'Arctic Amplification Study',
        authors: ['Jane Smith', 'John Doe'],
        year: 2022,
        url: 'https://doi.org/10.1000/arctic',
        doi: 'https://doi.org/10.1000/arctic',
        abstract_snippet: 'This study examines Arctic amplification mechanisms…',
      },
    ],
  }),
  saveReport: vi.fn().mockResolvedValue({ id: 'abc123' }),
}))

describe('ReportScanner', () => {
  beforeEach(() => vi.clearAllMocks())

  it('zeigt Abschnittstitel', async () => {
    render(<ReportScanner />)
    await waitFor(() =>
      expect(screen.getByText(/Wissenschaftliche Literatur scannen/i)).toBeInTheDocument()
    )
  })

  it('lädt und zeigt Themen-Dropdown', async () => {
    render(<ReportScanner />)
    await waitFor(() =>
      expect(screen.getByText(/Arktische Verstärkung/i)).toBeInTheDocument()
    )
  })

  it('zeigt Scan-Button', async () => {
    render(<ReportScanner />)
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Scan starten/i })).toBeInTheDocument()
    )
  })

  it('zeigt eigenes-Thema-Eingabefeld nach Auswahl', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getAllByRole('combobox'))
    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: '__custom__' } })
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/Arctic sea ice/i)).toBeInTheDocument()
    )
  })

  it('ruft scanReports beim Klick auf Scan-Button auf', async () => {
    const { scanReports } = await import('../api/client')
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() => expect(scanReports).toHaveBeenCalled())
  })

  it('zeigt Ergebnistitel nach Scan', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() =>
      expect(screen.getByText(/KI-Bericht:/i)).toBeInTheDocument()
    )
  })

  it('zeigt verwendete Artikel-Karten', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() =>
      expect(screen.getByText('Arctic Amplification Study')).toBeInTheDocument()
    )
  })

  it('zeigt Hauptautoren', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() =>
      expect(screen.getAllByText(/Jane Smith/).length).toBeGreaterThan(0)
    )
  })

  it('zeigt DOI-Link', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() => {
      const links = screen.getAllByRole('link')
      expect(links.some(l => l.href.includes('doi.org'))).toBe(true)
    })
  })

  it('zeigt Quellenhinweis-Banner', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() =>
      expect(screen.getByText(/ausschließlich/i)).toBeInTheDocument()
    )
  })

  it('zeigt KI-Badge bei LLM-Antwort', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() =>
      expect(screen.getByText(/Claude KI/i)).toBeInTheDocument()
    )
  })

  it('zeigt Speichern-Button nach Scan', async () => {
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Als Bericht speichern/i })).toBeInTheDocument()
    )
  })

  it('zeigt Fehlermeldung bei API-Fehler', async () => {
    const { scanReports } = await import('../api/client')
    scanReports.mockRejectedValueOnce(new Error('Netzwerkfehler'))
    render(<ReportScanner />)
    await waitFor(() => screen.getByRole('button', { name: /Scan starten/i }))
    fireEvent.click(screen.getByRole('button', { name: /Scan starten/i }))
    await waitFor(() =>
      expect(screen.getByText(/Netzwerkfehler/i)).toBeInTheDocument()
    )
  })
})

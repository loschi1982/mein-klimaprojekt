import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import ReportEditor from '../components/admin/ReportEditor'

vi.mock('../api/client', () => ({
  fetchAgentReport: vi.fn().mockResolvedValue({
    analyst: {
      summary: 'CO₂ steigt kontinuierlich.',
      findings: ['Anstieg seit 1958', 'Beschleunigung ab 2000'],
      recommendations: ['Emissionen reduzieren'],
    },
    trend_detector: {
      summary: 'Starker Aufwärtstrend.',
      findings: ['+2 ppm/Jahr im Schnitt'],
      recommendations: ['Monitoring fortsetzen'],
    },
  }),
  fetchReports: vi.fn().mockResolvedValue({
    count: 0,
    reports: [],
  }),
  saveReport: vi.fn().mockResolvedValue({ id: 'abc12345', created_at: '2026-01-01T00:00:00Z' }),
  updateReport: vi.fn().mockResolvedValue({ id: 'abc12345', updated_at: '2026-01-02T00:00:00Z' }),
  deleteReport: vi.fn().mockResolvedValue({ deleted: 'abc12345' }),
  getReport: vi.fn().mockResolvedValue({
    id: 'abc12345',
    title: 'Test',
    content: '<p>Inhalt</p>',
    source_id: 'esrl_mauna_loa',
    tags: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  }),
}))

describe('ReportEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('zeigt Überschrift', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByText(/Neuen Bericht erstellen/i)).toBeInTheDocument())
  })

  it('zeigt KI-Bericht-generieren-Button', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByText(/KI-Bericht generieren/i)).toBeInTheDocument())
  })

  it('zeigt Titel-Input', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByLabelText(/Titel/i)).toBeInTheDocument())
  })

  it('zeigt Datenquellen-Dropdown', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByLabelText(/Datenquelle/i)).toBeInTheDocument())
  })

  it('zeigt Tags-Input', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByLabelText(/Tags/i)).toBeInTheDocument())
  })

  it('zeigt WYSIWYG-Toolbar', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByRole('toolbar')).toBeInTheDocument())
  })

  it('zeigt Speichern-Button', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByText(/Bericht speichern/i)).toBeInTheDocument())
  })

  it('zeigt leere Berichte-Liste initial', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByText(/Noch keine Berichte/i)).toBeInTheDocument())
  })

  it('zeigt Berichte-Sektion', async () => {
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByText(/Gespeicherte Berichte/i)).toBeInTheDocument())
  })

  it('Toolbar enthält Fett-Button', async () => {
    render(<ReportEditor />)
    await waitFor(() => {
      const boldBtn = screen.getByTitle('Fett')
      expect(boldBtn).toBeInTheDocument()
    })
  })

  it('Toolbar enthält H2-Button', async () => {
    render(<ReportEditor />)
    await waitFor(() => {
      expect(screen.getByTitle('Überschrift 2')).toBeInTheDocument()
    })
  })

  it('KI-Bericht-Button ruft fetchAgentReport auf', async () => {
    const { fetchAgentReport } = await import('../api/client')
    render(<ReportEditor />)
    await waitFor(() => screen.getByText(/KI-Bericht generieren/i))
    fireEvent.click(screen.getByText(/KI-Bericht generieren/i))
    await waitFor(() => expect(fetchAgentReport).toHaveBeenCalled())
  })

  it('Speichern-Button ohne Inhalt zeigt Fehlermeldung', async () => {
    render(<ReportEditor />)
    await waitFor(() => screen.getByText(/Bericht speichern/i))
    fireEvent.click(screen.getByText(/Bericht speichern/i))
    await waitFor(() => expect(screen.getByText(/Bitte Titel und Inhalt/i)).toBeInTheDocument())
  })

  it('zeigt Berichte-Liste mit gespeicherten Berichten', async () => {
    const { fetchReports } = await import('../api/client')
    fetchReports.mockResolvedValue({
      count: 1,
      reports: [{
        id: 'abc12345',
        title: 'Mein Bericht',
        source_id: 'esrl_mauna_loa',
        tags: ['co2'],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      }],
    })
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByText('Mein Bericht')).toBeInTheDocument())
  })

  it('Löschen-Button ist sichtbar bei gespeichertem Bericht', async () => {
    const { fetchReports } = await import('../api/client')
    fetchReports.mockResolvedValue({
      count: 1,
      reports: [{
        id: 'abc12345',
        title: 'Zum Löschen',
        source_id: 'esrl_mauna_loa',
        tags: [],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      }],
    })
    render(<ReportEditor />)
    await waitFor(() => expect(screen.getByText('Löschen')).toBeInTheDocument())
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import SeaLevelChart from '../components/SeaLevelChart'

vi.mock('../api/client', () => ({
  fetchSeries: vi.fn().mockResolvedValue({
    source_id: 'csiro_sea_level',
    name: 'CSIRO – Globaler Meeresspiegel',
    unit: 'mm',
    series: [
      { date: '1880-01-01', value: -170.87 },
      { date: '1900-01-01', value: -120.50 },
      { date: '1950-01-01', value: -50.20 },
      { date: '1990-01-01', value: 0.0 },
      { date: '2000-06-01', value: 35.40 },
      { date: '2015-12-01', value: 68.23 },
    ],
  }),
}))

describe('SeaLevelChart', () => {
  beforeEach(() => vi.clearAllMocks())

  it('zeigt Ladeanzeige initial', () => {
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    expect(screen.getByText(/Lade Meeresspiegel/i)).toBeInTheDocument()
  })

  it('zeigt Überschrift nach dem Laden', async () => {
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    await waitFor(() =>
      expect(screen.getByText(/Globaler Meeresspiegel/i)).toBeInTheDocument()
    )
  })

  it('zeigt CSIRO als Quellenlink', async () => {
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /Church/i })
      expect(link).toBeInTheDocument()
    })
  })

  it('zeigt Einheit mm in der Untertitelzeile', async () => {
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    await waitFor(() => {
      const subtitle = screen.getByText(/Einheit: mm/i)
      expect(subtitle).toBeInTheDocument()
    })
  })

  it('zeigt Anstieg-Badge', async () => {
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    await waitFor(() =>
      expect(screen.getByText(/Anstieg/i)).toBeInTheDocument()
    )
  })

  it('zeigt Fußnote mit Quellenangabe', async () => {
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    await waitFor(() =>
      expect(screen.getByText(/Tide-Gauge/i)).toBeInTheDocument()
    )
  })

  it('zeigt Fehlermeldung bei Netzwerkfehler', async () => {
    const { fetchSeries } = await import('../api/client')
    fetchSeries.mockRejectedValueOnce(new Error('Network Error'))
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    await waitFor(() =>
      expect(screen.getByText(/Network Error/i)).toBeInTheDocument()
    )
  })

  it('zeigt Hinweis auf Import bei Fehler', async () => {
    const { fetchSeries } = await import('../api/client')
    fetchSeries.mockRejectedValueOnce(new Error('Not found'))
    render(<SeaLevelChart fromYear={1880} toYear={2015} />)
    await waitFor(() =>
      expect(screen.getByText(/csiro_sea_level/i)).toBeInTheDocument()
    )
  })

  it('ruft fetchSeries mit korrektem source_id auf', async () => {
    const { fetchSeries } = await import('../api/client')
    render(<SeaLevelChart fromYear={1950} toYear={2015} />)
    await waitFor(() => expect(fetchSeries).toHaveBeenCalledWith(
      'csiro_sea_level',
      '1950-01-01',
      '2015-12-31',
    ))
  })
})

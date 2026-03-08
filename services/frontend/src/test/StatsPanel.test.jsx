import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import StatsPanel from '../components/StatsPanel'
import * as client from '../api/client'

const MOCK_STATS = {
  slope: 2.1,
  mean: 390.5,
  max_value: 428.6,
  min_value: 315.0,
  count: 800,
  anomaly_count: 3,
  min_date: '1958-03-01',
  max_date: '2026-01-01',
}

describe('StatsPanel', () => {
  it('zeigt Ladeanzeige initial', () => {
    vi.spyOn(client, 'fetchCo2Stats').mockReturnValue(new Promise(() => {}))
    render(<StatsPanel />)
    expect(screen.getByText(/Lade Statistiken/i)).toBeInTheDocument()
  })

  it('zeigt Fehlermeldung bei API-Fehler', async () => {
    vi.spyOn(client, 'fetchCo2Stats').mockRejectedValue(new Error('API Error'))
    render(<StatsPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Fehler/i)).toBeInTheDocument()
    })
  })

  it('zeigt Maximalwert nach Laden', async () => {
    vi.spyOn(client, 'fetchCo2Stats').mockResolvedValue(MOCK_STATS)
    render(<StatsPanel />)
    await waitFor(() => {
      expect(screen.getByText(/428\.6/)).toBeInTheDocument()
    })
  })

  it('zeigt Trendwert nach Laden', async () => {
    vi.spyOn(client, 'fetchCo2Stats').mockResolvedValue(MOCK_STATS)
    render(<StatsPanel />)
    await waitFor(() => {
      expect(screen.getByText(/2\.10/)).toBeInTheDocument()
    })
  })

  it('zeigt Anzahl der Messpunkte', async () => {
    vi.spyOn(client, 'fetchCo2Stats').mockResolvedValue(MOCK_STATS)
    render(<StatsPanel />)
    await waitFor(() => {
      expect(screen.getByText('800')).toBeInTheDocument()
    })
  })

  it('zeigt Anomalieanzahl', async () => {
    vi.spyOn(client, 'fetchCo2Stats').mockResolvedValue(MOCK_STATS)
    render(<StatsPanel />)
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument()
    })
  })

  it('zeigt Chart-Titel', async () => {
    vi.spyOn(client, 'fetchCo2Stats').mockResolvedValue(MOCK_STATS)
    render(<StatsPanel />)
    await waitFor(() => {
      expect(screen.getByText(/CO₂-Statistiken/i)).toBeInTheDocument()
    })
  })

  it('zeigt Schwellenwert-Legende', async () => {
    vi.spyOn(client, 'fetchCo2Stats').mockResolvedValue(MOCK_STATS)
    render(<StatsPanel />)
    await waitFor(() => {
      expect(screen.getByText(/Sicherheitsgrenze/i)).toBeInTheDocument()
    })
  })
})

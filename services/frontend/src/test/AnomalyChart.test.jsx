import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import AnomalyChart from '../components/AnomalyChart'
import * as client from '../api/client'

const MOCK_ANOMALIES = {
  anomalies: [
    { date: '1991-06-01', value: 356.9, z_score: 2.8, severity: 'warning' },
    { date: '1998-05-01', value: 369.5, z_score: 3.5, severity: 'critical' },
  ],
}

describe('AnomalyChart', () => {
  it('zeigt Ladeanzeige initial', () => {
    vi.spyOn(client, 'fetchAnomalies').mockReturnValue(new Promise(() => {}))
    render(<AnomalyChart threshold={2.0} />)
    expect(screen.getByText(/Lade Anomalie/i)).toBeInTheDocument()
  })

  it('zeigt Fehlermeldung bei API-Fehler', async () => {
    vi.spyOn(client, 'fetchAnomalies').mockRejectedValue(new Error('API Error'))
    render(<AnomalyChart />)
    await waitFor(() => {
      expect(screen.getByText(/Fehler/i)).toBeInTheDocument()
    })
  })

  it('zeigt Chart-Titel nach Laden', async () => {
    vi.spyOn(client, 'fetchAnomalies').mockResolvedValue(MOCK_ANOMALIES)
    render(<AnomalyChart threshold={2.0} />)
    await waitFor(() => {
      expect(screen.getByText(/CO₂-Anomalien/i)).toBeInTheDocument()
    })
  })

  it('zeigt Z-Score-Schwellenwert im Titel', async () => {
    vi.spyOn(client, 'fetchAnomalies').mockResolvedValue(MOCK_ANOMALIES)
    render(<AnomalyChart threshold={2.5} />)
    await waitFor(() => {
      expect(screen.getByText(/2\.5/)).toBeInTheDocument()
    })
  })

  it('zeigt Anzahl der Anomalien', async () => {
    vi.spyOn(client, 'fetchAnomalies').mockResolvedValue(MOCK_ANOMALIES)
    render(<AnomalyChart threshold={2.0} />)
    await waitFor(() => {
      expect(screen.getByText(/2 statistische Ausreißer/i)).toBeInTheDocument()
    })
  })

  it('zeigt Hinweis bei leerer Anomalienliste', async () => {
    vi.spyOn(client, 'fetchAnomalies').mockResolvedValue({ anomalies: [] })
    render(<AnomalyChart threshold={2.0} />)
    await waitFor(() => {
      expect(screen.getByText(/Keine Anomalien/i)).toBeInTheDocument()
    })
  })

  it('zeigt Severity-Legende', async () => {
    vi.spyOn(client, 'fetchAnomalies').mockResolvedValue(MOCK_ANOMALIES)
    render(<AnomalyChart threshold={2.0} />)
    await waitFor(() => {
      expect(screen.getByText('critical')).toBeInTheDocument()
      expect(screen.getByText('warning')).toBeInTheDocument()
    })
  })
})

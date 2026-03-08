import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import SimulationChart from '../components/SimulationChart'
import * as client from '../api/client'

const MOCK_COMPARISON = {
  rcp26: {
    scenario_name: 'RCP 2.6',
    projection: [
      { year: 2026, co2_ppm: 428.0, temperature_anomaly_c: 1.1, radiative_forcing_wm2: 2.3 },
      { year: 2030, co2_ppm: 430.0, temperature_anomaly_c: 1.15, radiative_forcing_wm2: 2.4 },
    ],
    summary: {},
  },
  rcp85: {
    scenario_name: 'RCP 8.5',
    projection: [
      { year: 2026, co2_ppm: 428.0, temperature_anomaly_c: 1.1, radiative_forcing_wm2: 2.3 },
      { year: 2030, co2_ppm: 442.0, temperature_anomaly_c: 1.3, radiative_forcing_wm2: 2.7 },
    ],
    summary: {},
  },
}

describe('SimulationChart', () => {
  it('zeigt Ladeanzeige initial', () => {
    vi.spyOn(client, 'compareScenarios').mockReturnValue(new Promise(() => {}))
    render(<SimulationChart years={50} />)
    expect(screen.getByText(/Lade Simulation/i)).toBeInTheDocument()
  })

  it('zeigt Fehlermeldung bei API-Fehler', async () => {
    vi.spyOn(client, 'compareScenarios').mockRejectedValue(new Error('API Error'))
    render(<SimulationChart />)
    await waitFor(() => {
      expect(screen.getByText(/Fehler/i)).toBeInTheDocument()
    })
  })

  it('zeigt Chart-Titel nach Laden', async () => {
    vi.spyOn(client, 'compareScenarios').mockResolvedValue(MOCK_COMPARISON)
    render(<SimulationChart years={50} />)
    await waitFor(() => {
      expect(screen.getByText(/RCP-Szenario-Vergleich/i)).toBeInTheDocument()
    })
  })

  it('zeigt Zeitraum im Subtitle', async () => {
    vi.spyOn(client, 'compareScenarios').mockResolvedValue(MOCK_COMPARISON)
    render(<SimulationChart years={75} />)
    await waitFor(() => {
      expect(screen.getByText(/75 Jahre/i)).toBeInTheDocument()
    })
  })

  it('zeigt Szenario-Badges', async () => {
    vi.spyOn(client, 'compareScenarios').mockResolvedValue(MOCK_COMPARISON)
    render(<SimulationChart years={50} />)
    await waitFor(() => {
      expect(screen.getByText('RCP 2.6')).toBeInTheDocument()
      expect(screen.getByText('RCP 8.5')).toBeInTheDocument()
    })
  })
})

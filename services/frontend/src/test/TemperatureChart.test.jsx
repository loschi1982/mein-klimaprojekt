import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import TemperatureChart from '../components/TemperatureChart'
import * as client from '../api/client'

const MOCK_DATA = {
  name: 'NASA GISS – Globale Temperaturanomalie',
  unit: '°C',
  source_url: 'https://data.giss.nasa.gov/gistemp/',
  count: 3,
  series: [
    { date: '1960-01-01', value: -0.02 },
    { date: '2000-01-01', value: 0.42 },
    { date: '2024-01-01', value: 1.13 },
  ],
}

describe('TemperatureChart', () => {
  it('zeigt Ladeanzeige initial', () => {
    vi.spyOn(client, 'fetchTemperature').mockReturnValue(new Promise(() => {}))
    render(<TemperatureChart fromYear={1960} toYear={2024} />)
    expect(screen.getByText(/Lade Temperaturdaten/i)).toBeInTheDocument()
  })

  it('zeigt Fehlermeldung bei API-Fehler', async () => {
    vi.spyOn(client, 'fetchTemperature').mockRejectedValue(new Error('Nicht gefunden'))
    render(<TemperatureChart fromYear={1960} toYear={2024} />)
    await waitFor(() => {
      expect(screen.getByText(/Fehler/i)).toBeInTheDocument()
    })
  })

  it('zeigt Hinweis auf Admin-Import bei Fehler', async () => {
    vi.spyOn(client, 'fetchTemperature').mockRejectedValue(new Error('404'))
    render(<TemperatureChart fromYear={1960} toYear={2024} />)
    await waitFor(() => {
      expect(screen.getByText(/Admin/i)).toBeInTheDocument()
    })
  })

  it('zeigt Chart-Titel nach Laden', async () => {
    vi.spyOn(client, 'fetchTemperature').mockResolvedValue(MOCK_DATA)
    render(<TemperatureChart fromYear={1960} toYear={2024} />)
    await waitFor(() => {
      expect(screen.getByText(/Globale Temperaturanomalie/i)).toBeInTheDocument()
    })
  })

  it('zeigt klickbaren NASA GISS Link', async () => {
    vi.spyOn(client, 'fetchTemperature').mockResolvedValue(MOCK_DATA)
    render(<TemperatureChart fromYear={1960} toYear={2024} sourceUrl="https://data.giss.nasa.gov/gistemp/" />)
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /NASA GISS/i })
      expect(link).toHaveAttribute('href', 'https://data.giss.nasa.gov/gistemp/')
      expect(link).toHaveAttribute('target', '_blank')
    })
  })

  it('zeigt Referenzperiode 1951–1980', async () => {
    vi.spyOn(client, 'fetchTemperature').mockResolvedValue(MOCK_DATA)
    render(<TemperatureChart fromYear={1960} toYear={2024} />)
    await waitFor(() => {
      expect(screen.getAllByText(/1951/).length).toBeGreaterThan(0)
    })
  })

  it('zeigt Anomalie-Erklärung', async () => {
    vi.spyOn(client, 'fetchTemperature').mockResolvedValue(MOCK_DATA)
    render(<TemperatureChart fromYear={1960} toYear={2024} />)
    await waitFor(() => {
      expect(screen.getByText(/Abweichung vom Mittelwert/i)).toBeInTheDocument()
    })
  })

  it('ruft fetchTemperature mit korrekten Datumsgrenzen auf', async () => {
    const spy = vi.spyOn(client, 'fetchTemperature').mockResolvedValue(MOCK_DATA)
    render(<TemperatureChart fromYear={1980} toYear={2020} />)
    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith('1980-01-01', '2020-12-31')
    })
  })
})

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

vi.mock('../api/client', () => ({
  fetchCo2Data: vi.fn().mockResolvedValue([]),
  fetchSeries: vi.fn().mockResolvedValue({ series: [], unit: 'ppm', name: 'Test', source_url: '' }),
  fetchTemperature: vi.fn().mockResolvedValue({ series: [], unit: '°C', name: 'Test', source_url: '' }),
  fetchCo2Stats: vi.fn().mockResolvedValue({ slope: 2.1, mean: 390.5, max_value: 428.6, min_value: 315.0, count: 800, anomaly_count: 3, min_date: '1958-03-01', max_date: '2026-01-01' }),
  fetchAnomalies: vi.fn().mockResolvedValue({ anomalies: [] }),
  compareScenarios: vi.fn().mockResolvedValue({}),
  fetchSources: vi.fn().mockResolvedValue([]),
  ingestSource: vi.fn().mockResolvedValue({ status: 'done', file: 'test.csv' }),
  fetchDatasets: vi.fn().mockResolvedValue([]),
}))

describe('App', () => {
  it('rendert den Header', () => {
    render(<App />)
    expect(screen.getByText('Klimadaten-Dashboard')).toBeInTheDocument()
  })

  it('zeigt Navbar mit Hauptmenüpunkten', () => {
    render(<App />)
    expect(screen.getByText('Klimadaten')).toBeInTheDocument()
    expect(screen.getByText('Temperaturen')).toBeInTheDocument()
    expect(screen.getByText('Analyse')).toBeInTheDocument()
  })

  it('zeigt den Zeitraum-Slider', () => {
    render(<App />)
    expect(screen.getByText('Zeitraum')).toBeInTheDocument()
  })

  it('zeigt Footer mit Datenquellen-Links', () => {
    render(<App />)
    expect(screen.getByText('NOAA GML')).toBeInTheDocument()
    expect(screen.getByText('NASA GISS')).toBeInTheDocument()
    expect(screen.getByText('IPCC')).toBeInTheDocument()
  })

  it('Footer NOAA-Link hat korrekten href', () => {
    render(<App />)
    const link = screen.getByText('NOAA GML').closest('a')
    expect(link).toHaveAttribute('href')
    expect(link.getAttribute('href')).toContain('noaa')
  })

  it('rendert ohne Fehler', () => {
    expect(() => render(<App />)).not.toThrow()
  })

  it('Slider hat zwei Range-Inputs', () => {
    render(<App />)
    const sliders = screen.getAllByRole('slider')
    expect(sliders.length).toBeGreaterThanOrEqual(2)
  })
})

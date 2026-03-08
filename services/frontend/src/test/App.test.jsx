import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from '../App'

// Mock alle API-Calls
vi.mock('../api/client', () => ({
  fetchCo2Data: vi.fn().mockResolvedValue([]),
  fetchCo2Stats: vi.fn().mockResolvedValue({
    slope: 2.1,
    mean: 390.5,
    max_value: 428.6,
    min_value: 315.0,
    count: 800,
    anomaly_count: 3,
    min_date: '1958-03-01',
    max_date: '2026-01-01',
  }),
  fetchAnomalies: vi.fn().mockResolvedValue({ anomalies: [] }),
  compareScenarios: vi.fn().mockResolvedValue({}),
}))

describe('App', () => {
  it('rendert den Header', () => {
    render(<App />)
    expect(screen.getByText('Klimadaten-Dashboard')).toBeInTheDocument()
  })

  it('zeigt alle vier Tabs', () => {
    render(<App />)
    expect(screen.getByText('CO₂-Verlauf')).toBeInTheDocument()
    expect(screen.getByText('Szenarien')).toBeInTheDocument()
    expect(screen.getByText('Statistiken')).toBeInTheDocument()
    expect(screen.getByText('Anomalien')).toBeInTheDocument()
  })

  it('Tab CO₂-Verlauf ist standardmäßig aktiv', () => {
    render(<App />)
    const activeTab = screen.getByText('CO₂-Verlauf')
    expect(activeTab.className).toContain('tab-btn--active')
  })

  it('Klick auf Szenarien-Tab wechselt den aktiven Tab', () => {
    render(<App />)
    const tab = screen.getByText('Szenarien')
    fireEvent.click(tab)
    expect(tab.className).toContain('tab-btn--active')
  })

  it('Klick auf Statistiken-Tab wechselt den aktiven Tab', () => {
    render(<App />)
    fireEvent.click(screen.getByText('Statistiken'))
    expect(screen.getByText('Statistiken').className).toContain('tab-btn--active')
  })

  it('Klick auf Anomalien-Tab wechselt den aktiven Tab', () => {
    render(<App />)
    fireEvent.click(screen.getByText('Anomalien'))
    expect(screen.getByText('Anomalien').className).toContain('tab-btn--active')
  })

  it('zeigt Footer mit Datenquellen', () => {
    render(<App />)
    expect(screen.getByText(/NOAA ESRL/)).toBeInTheDocument()
  })

  it('rendert ohne Fehler', () => {
    expect(() => render(<App />)).not.toThrow()
  })
})

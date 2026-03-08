import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import Co2Chart from '../components/Co2Chart'
import * as client from '../api/client'

describe('Co2Chart', () => {
  it('zeigt Ladeanzeige initial', () => {
    vi.spyOn(client, 'fetchCo2Data').mockReturnValue(new Promise(() => {}))
    render(<Co2Chart />)
    expect(screen.getByText(/Lade CO₂/i)).toBeInTheDocument()
  })

  it('zeigt Fehlermeldung bei API-Fehler', async () => {
    vi.spyOn(client, 'fetchCo2Data').mockRejectedValue(new Error('Netzwerkfehler'))
    render(<Co2Chart />)
    await waitFor(() => {
      expect(screen.getByText(/Fehler/i)).toBeInTheDocument()
    })
  })

  it('zeigt Chart-Titel nach erfolgreicher Anfrage', async () => {
    vi.spyOn(client, 'fetchCo2Data').mockResolvedValue([
      { date: '1960-01-01', value: 316.5 },
      { date: '1960-06-01', value: 317.2 },
      { date: '2020-01-01', value: 412.5 },
    ])
    render(<Co2Chart />)
    await waitFor(() => {
      expect(screen.getByText(/CO₂-Konzentration/i)).toBeInTheDocument()
    })
  })

  it('zeigt leeren Chart bei leerer Datenserie', async () => {
    vi.spyOn(client, 'fetchCo2Data').mockResolvedValue([])
    render(<Co2Chart />)
    await waitFor(() => {
      expect(screen.getByText(/CO₂-Konzentration/i)).toBeInTheDocument()
    })
  })
})

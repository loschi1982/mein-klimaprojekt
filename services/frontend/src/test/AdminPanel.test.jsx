import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import AdminPanel from '../components/AdminPanel'
import * as client from '../api/client'

vi.mock('../api/client', () => ({
  fetchSources: vi.fn().mockResolvedValue([
    { id: 'esrl_mauna_loa', name: 'ESRL Mauna Loa CO₂', format: 'csv', unit: 'ppm', description: 'Monatliche CO₂-Konzentration' },
    { id: 'esrl_ch4', name: 'ESRL Methan (CH₄)', format: 'csv', unit: 'ppb', description: 'Globaler Methan-Mittelwert' },
  ]),
  ingestSource: vi.fn().mockResolvedValue({ status: 'done', file: 'esrl_mauna_loa.csv' }),
  fetchDatasets: vi.fn().mockResolvedValue([
    { name: 'esrl_mauna_loa.csv', rows: 780, columns: ['date', 'value'], date_range: { min: '1958-03', max: '2024-12' } },
  ]),
}))

beforeEach(() => {
  sessionStorage.clear()
})

describe('AdminPanel – Login', () => {
  it('zeigt Login-Formular wenn nicht angemeldet', () => {
    render(<AdminPanel />)
    expect(screen.getByText('Admin-Bereich')).toBeInTheDocument()
    expect(screen.getByLabelText('Benutzername')).toBeInTheDocument()
    expect(screen.getByLabelText('Passwort')).toBeInTheDocument()
  })

  it('zeigt Fehler bei falschen Zugangsdaten', () => {
    render(<AdminPanel />)
    fireEvent.change(screen.getByLabelText('Benutzername'), { target: { value: 'wrong' } })
    fireEvent.change(screen.getByLabelText('Passwort'), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByText('Anmelden'))
    expect(screen.getByText(/falsch/i)).toBeInTheDocument()
  })

  it('meldet sich bei korrekten Zugangsdaten an', async () => {
    render(<AdminPanel />)
    fireEvent.change(screen.getByLabelText('Benutzername'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('Passwort'), { target: { value: '1234' } })
    fireEvent.click(screen.getByText('Anmelden'))
    await waitFor(() => {
      expect(screen.getByText('Abmelden')).toBeInTheDocument()
    })
  })

  it('speichert Auth in sessionStorage nach Login', () => {
    render(<AdminPanel />)
    fireEvent.change(screen.getByLabelText('Benutzername'), { target: { value: 'admin' } })
    fireEvent.change(screen.getByLabelText('Passwort'), { target: { value: '1234' } })
    fireEvent.click(screen.getByText('Anmelden'))
    expect(sessionStorage.getItem('admin_auth')).toBe('1')
  })

  it('zeigt Admin-Panel direkt wenn bereits angemeldet', async () => {
    sessionStorage.setItem('admin_auth', '1')
    render(<AdminPanel />)
    await waitFor(() => {
      expect(screen.getByText('Abmelden')).toBeInTheDocument()
    })
  })

  it('meldet ab und zeigt wieder Login-Formular', async () => {
    sessionStorage.setItem('admin_auth', '1')
    render(<AdminPanel />)
    await waitFor(() => screen.getByText('Abmelden'))
    fireEvent.click(screen.getByText('Abmelden'))
    expect(screen.getByLabelText('Benutzername')).toBeInTheDocument()
    expect(sessionStorage.getItem('admin_auth')).toBeNull()
  })
})

describe('AdminPanel – nach Login', () => {
  beforeEach(() => {
    sessionStorage.setItem('admin_auth', '1')
  })

  it('zeigt Datenquellen nach Login', async () => {
    render(<AdminPanel />)
    await waitFor(() => {
      expect(screen.getByText('ESRL Mauna Loa CO₂')).toBeInTheDocument()
    })
  })

  it('zeigt Import-Buttons für alle Quellen', async () => {
    render(<AdminPanel />)
    await waitFor(() => {
      const buttons = screen.getAllByText('Importieren')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })

  it('zeigt importierte Datensätze', async () => {
    render(<AdminPanel />)
    await waitFor(() => {
      expect(screen.getByText('esrl_mauna_loa.csv')).toBeInTheDocument()
    })
  })

  it('zeigt Zeilenanzahl im Datensatz', async () => {
    render(<AdminPanel />)
    await waitFor(() => {
      expect(screen.getByText('780')).toBeInTheDocument()
    })
  })

  it('ruft ingestSource auf beim Klick auf Importieren', async () => {
    render(<AdminPanel />)
    await waitFor(() => screen.getAllByText('Importieren'))
    fireEvent.click(screen.getAllByText('Importieren')[0])
    await waitFor(() => {
      expect(client.ingestSource).toHaveBeenCalled()
    })
  })

  it('zeigt Erfolgsstatus nach Import', async () => {
    render(<AdminPanel />)
    await waitFor(() => screen.getAllByText('Importieren'))
    fireEvent.click(screen.getAllByText('Importieren')[0])
    await waitFor(() => {
      expect(screen.getByText(/esrl_mauna_loa\.csv/i)).toBeInTheDocument()
    })
  })
})

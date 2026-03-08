import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import NavBar from '../components/NavBar'
import { AppProvider } from '../context/AppContext'

const renderWithCtx = () => render(<AppProvider><NavBar /></AppProvider>)

describe('NavBar', () => {
  it('zeigt alle Hauptmenü-Punkte', () => {
    renderWithCtx()
    expect(screen.getByText('Klimadaten')).toBeInTheDocument()
    expect(screen.getByText('Temperaturen')).toBeInTheDocument()
    expect(screen.getByText('Analyse')).toBeInTheDocument()
    expect(screen.getByText(/Admin/)).toBeInTheDocument()
  })

  it('öffnet Dropdown bei Hover auf Klimadaten', () => {
    renderWithCtx()
    fireEvent.mouseEnter(screen.getByText('Klimadaten').closest('.nav-item'))
    expect(screen.getByText('CO₂ – Mauna Loa')).toBeInTheDocument()
    expect(screen.getByText('Methan (CH₄)')).toBeInTheDocument()
  })

  it('zeigt Einheit ppb für CH₄ im Dropdown', () => {
    renderWithCtx()
    fireEvent.mouseEnter(screen.getByText('Klimadaten').closest('.nav-item'))
    expect(screen.getByText('ppb')).toBeInTheDocument()
  })

  it('öffnet Temperatur-Dropdown', () => {
    renderWithCtx()
    fireEvent.mouseEnter(screen.getByText('Temperaturen').closest('.nav-item'))
    expect(screen.getByText('Global (NASA GISS)')).toBeInTheDocument()
  })

  it('öffnet Analyse-Dropdown', () => {
    renderWithCtx()
    fireEvent.mouseEnter(screen.getByText('Analyse').closest('.nav-item'))
    expect(screen.getByText('Statistiken')).toBeInTheDocument()
    expect(screen.getByText('Anomalien')).toBeInTheDocument()
  })

  it('schließt Dropdown nach MouseLeave', () => {
    renderWithCtx()
    const item = screen.getByText('Klimadaten').closest('.nav-item')
    fireEvent.mouseEnter(item)
    expect(screen.getByText('CO₂ – Mauna Loa')).toBeInTheDocument()
    fireEvent.mouseLeave(item)
    expect(screen.queryByText('CO₂ – Mauna Loa')).not.toBeInTheDocument()
  })
})

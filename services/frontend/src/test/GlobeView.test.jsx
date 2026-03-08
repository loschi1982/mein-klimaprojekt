import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import GlobeView from '../components/GlobeView'

// react-globe.gl requires WebGL/Three.js – mock it for JSDOM
vi.mock('react-globe.gl', () => ({
  default: vi.fn(({ polygonsData }) => (
    <div data-testid="globe-mock">
      Globe ({polygonsData?.length ?? 0} Polygone)
    </div>
  )),
}))

// Mock API
vi.mock('../api/client', () => ({
  fetchZonalTemperature: vi.fn().mockResolvedValue({
    zones: ['Glob', 'NHem', 'SHem', '24N-90N', '24S-24N', '90S-24S',
            '64N-90N', '44N-64N', '24N-44N', 'EQU-24N', '24S-EQU',
            '44S-24S', '64S-44S', '90S-64S'],
    data: [
      { year: 2020, Glob: 1.02, NHem: 1.25, SHem: 0.79,
        '24N-90N': 1.55, '24S-24N': 0.82, '90S-24S': 0.58,
        '64N-90N': 2.10, '44N-64N': 1.40, '24N-44N': 1.20,
        'EQU-24N': 0.75, '24S-EQU': 0.70, '44S-24S': 0.55,
        '64S-44S': 0.50, '90S-64S': 0.40 },
    ],
  }),
  fetchCo2Annual: vi.fn().mockResolvedValue({
    unit: 'ppm',
    count: 1,
    series: [{ year: 2020, value: 412.45 }],
  }),
}))

// Mock fetch for GeoJSON
beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    json: () => Promise.resolve({ features: [
      { type: 'Feature', properties: { NAME: 'Germany', LABEL_Y: 51 }, geometry: {} },
    ] }),
  })
})

describe('GlobeView', () => {
  it('zeigt Ladeanzeige initial', () => {
    render(<GlobeView />)
    expect(screen.getByText(/laden/i)).toBeInTheDocument()
  })

  it('zeigt Globus nach dem Laden', async () => {
    render(<GlobeView />)
    await waitFor(() => expect(screen.getByTestId('globe-mock')).toBeInTheDocument())
  })

  it('zeigt Überschrift', async () => {
    render(<GlobeView />)
    await waitFor(() => expect(screen.getByText(/3D-Globus/i)).toBeInTheDocument())
  })

  it('zeigt CO₂-Overlay-Wert', async () => {
    render(<GlobeView />)
    await waitFor(() => expect(screen.getByText(/412\.4/)).toBeInTheDocument())
  })

  it('zeigt Play/Pause-Button', async () => {
    render(<GlobeView />)
    await waitFor(() => expect(screen.getByText(/Abspielen/i)).toBeInTheDocument())
  })

  it('zeigt Jahreslabel im Slider', async () => {
    render(<GlobeView />)
    await waitFor(() => {
      const labels = screen.getAllByText('2020')
      expect(labels.length).toBeGreaterThan(0)
    })
  })

  it('zeigt zonale Tabelle mit Werten', async () => {
    render(<GlobeView />)
    await waitFor(() => {
      expect(screen.getByText('64N-90N')).toBeInTheDocument()
      expect(screen.getByText('+2.10')).toBeInTheDocument()
    })
  })

  it('zeigt globalen Mittelwert', async () => {
    render(<GlobeView />)
    await waitFor(() => {
      expect(screen.getByText('Global')).toBeInTheDocument()
      expect(screen.getByText('+1.02')).toBeInTheDocument()
    })
  })

  it('Jahresslider ändert Jahr', async () => {
    render(<GlobeView />)
    await waitFor(() => screen.getByRole('slider'))
    const slider = screen.getByRole('slider')
    fireEvent.change(slider, { target: { value: '1990' } })
    expect(screen.getAllByText('1990').length).toBeGreaterThan(0)
  })

  it('Play-Button wechselt zu Pause', async () => {
    render(<GlobeView />)
    await waitFor(() => screen.getByText(/Abspielen/i))
    fireEvent.click(screen.getByText(/Abspielen/i))
    expect(screen.getByText(/Pause/i)).toBeInTheDocument()
  })
})

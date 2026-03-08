import { AppProvider, useAppContext } from './context/AppContext'
import NavBar from './components/NavBar'
import TimeRangeSlider from './components/TimeRangeSlider'
import ClimateSeriesChart from './components/ClimateSeriesChart'
import TemperatureChart from './components/TemperatureChart'
import SeaLevelChart from './components/SeaLevelChart'
import SimulationChart from './components/SimulationChart'
import StatsPanel from './components/StatsPanel'
import AnomalyChart from './components/AnomalyChart'
import AdminPanel from './components/AdminPanel'
import GlobeView from './components/GlobeView'
import './App.css'

// Views die ClimateSeriesChart verwenden (sourceId → backend source_id)
const SOURCE_MAP = {
  co2_mauna_loa: 'esrl_mauna_loa',
  co2_global: 'esrl_co2_global',
  ch4: 'esrl_ch4',
  temp_berkeley: 'berkeley_earth_global',
}

function Dashboard() {
  const { currentView, timeRange, setTimeRange } = useAppContext()
  const viewId = currentView.id
  const [fromYear, toYear] = timeRange

  const showSlider = !['admin', 'simulation', 'globe'].includes(viewId)

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-content">
          <div>
            <h1>Klimadaten-Dashboard</h1>
            <p>KI-gestützte Analyse und Visualisierung von Klimadaten</p>
          </div>
        </div>
      </header>

      <NavBar />

      {showSlider && (
        <div className="slider-bar">
          <TimeRangeSlider value={timeRange} onChange={setTimeRange} />
        </div>
      )}

      <main className="app-main">
        <section className="section">
          {SOURCE_MAP[viewId] && (
            <ClimateSeriesChart
              sourceId={SOURCE_MAP[viewId]}
              fromYear={fromYear}
              toYear={toYear}
            />
          )}
          {viewId === 'temp_global' && (
            <TemperatureChart
              fromYear={fromYear}
              toYear={toYear}
              sourceUrl="https://data.giss.nasa.gov/gistemp/"
            />
          )}
          {viewId === 'sea_level' && (
            <SeaLevelChart fromYear={fromYear} toYear={toYear} />
          )}
          {viewId === 'globe' && <GlobeView />}
          {viewId === 'simulation' && <SimulationChart years={75} />}
          {viewId === 'stats' && <StatsPanel />}
          {viewId === 'anomalies' && <AnomalyChart threshold={2.0} />}
          {viewId === 'admin' && <AdminPanel />}
        </section>
      </main>

      <footer className="app-footer">
        <p>
          Datenquellen:{' '}
          <a href="https://gml.noaa.gov/ccgg/trends/" target="_blank" rel="noreferrer" className="source-link">NOAA GML</a>
          {' · '}
          <a href="https://data.giss.nasa.gov/gistemp/" target="_blank" rel="noreferrer" className="source-link">NASA GISS</a>
          {' · '}
          <a href="https://berkeleyearth.org/data/" target="_blank" rel="noreferrer" className="source-link">Berkeley Earth</a>
          {' · '}
          <a href="https://www.cmar.csiro.au/sealevel/" target="_blank" rel="noreferrer" className="source-link">CSIRO</a>
          {' · '}
          <a href="https://www.ipcc.ch/" target="_blank" rel="noreferrer" className="source-link">IPCC</a>
        </p>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <AppProvider>
      <Dashboard />
    </AppProvider>
  )
}

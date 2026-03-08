import { useState } from 'react'
import Co2Chart from './components/Co2Chart'
import SimulationChart from './components/SimulationChart'
import StatsPanel from './components/StatsPanel'
import AnomalyChart from './components/AnomalyChart'
import './App.css'

const TABS = [
  { id: 'co2', label: 'CO₂-Verlauf' },
  { id: 'simulation', label: 'Szenarien' },
  { id: 'stats', label: 'Statistiken' },
  { id: 'anomalies', label: 'Anomalien' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('co2')

  return (
    <div className="app">
      <header className="app-header">
        <h1>Klimadaten-Dashboard</h1>
        <p>KI-gestützte Analyse und Visualisierung von Klimadaten</p>
      </header>

      <nav className="tab-nav">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn${activeTab === tab.id ? ' tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        <section className="section">
          {activeTab === 'co2' && <Co2Chart />}
          {activeTab === 'simulation' && <SimulationChart years={75} />}
          {activeTab === 'stats' && <StatsPanel />}
          {activeTab === 'anomalies' && <AnomalyChart threshold={2.0} />}
        </section>
      </main>

      <footer className="app-footer">
        <p>Datenquellen: NOAA ESRL · Mauna Loa Observatory · IPCC RCP-Szenarien</p>
      </footer>
    </div>
  )
}

import Co2Chart from './components/Co2Chart'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Klimadaten-Dashboard</h1>
        <p>KI-gestützte Analyse und Visualisierung von Klimadaten</p>
      </header>

      <main className="app-main">
        <section className="section">
          <Co2Chart />
        </section>
      </main>

      <footer className="app-footer">
        <p>Datenquellen: NOAA ESRL · Mauna Loa Observatory</p>
      </footer>
    </div>
  )
}

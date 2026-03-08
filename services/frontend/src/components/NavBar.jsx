import { useState, useRef, useEffect } from 'react'
import { useAppContext } from '../context/AppContext'

export const NAV_ITEMS = [
  {
    id: 'climate',
    label: 'Klimadaten',
    children: [
      { id: 'co2_mauna_loa', label: 'CO₂ – Mauna Loa', unit: 'ppm', sourceId: 'esrl_mauna_loa' },
      { id: 'co2_global', label: 'CO₂ – Global', unit: 'ppm', sourceId: 'esrl_co2_global' },
      { id: 'ch4', label: 'Methan (CH₄)', unit: 'ppb', sourceId: 'esrl_ch4' },
    ],
  },
  {
    id: 'temperature',
    label: 'Temperaturen',
    children: [
      { id: 'temp_global', label: 'Global (NASA GISS)', unit: '°C', sourceId: 'nasa_giss_global' },
      { id: 'globe', label: '3D-Globus (Zonen)', unit: '°C', sourceId: 'nasa_giss_zonal' },
    ],
  },
  {
    id: 'analysis',
    label: 'Analyse',
    children: [
      { id: 'stats', label: 'Statistiken' },
      { id: 'anomalies', label: 'Anomalien' },
      { id: 'simulation', label: 'RCP-Szenarien' },
    ],
  },
  {
    id: 'admin',
    label: '⚙ Admin',
    children: null,
  },
]

function DropdownMenu({ items, onSelect, activeId }) {
  return (
    <ul className="dropdown-menu">
      {items.map(item => (
        <li key={item.id}>
          <button
            className={`dropdown-item${activeId === item.id ? ' dropdown-item--active' : ''}`}
            onClick={() => onSelect(item)}
          >
            <span>{item.label}</span>
            {item.unit && <span className="dropdown-unit">{item.unit}</span>}
          </button>
        </li>
      ))}
    </ul>
  )
}

function NavItem({ item, activeId, onSelect }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const isActive = item.children
    ? item.children.some(c => c.id === activeId)
    : item.id === activeId

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  if (!item.children) {
    return (
      <button
        className={`nav-btn${isActive ? ' nav-btn--active nav-btn--admin' : ' nav-btn--admin'}`}
        onClick={() => onSelect(item)}
      >
        {item.label}
      </button>
    )
  }

  return (
    <div
      className={`nav-item${isActive ? ' nav-item--active' : ''}`}
      ref={ref}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        className={`nav-btn${isActive ? ' nav-btn--active' : ''}`}
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-haspopup="true"
      >
        {item.label}
        <span className={`nav-arrow${open ? ' nav-arrow--open' : ''}`}>▾</span>
      </button>
      {open && (
        <DropdownMenu
          items={item.children}
          onSelect={child => { onSelect(child); setOpen(false) }}
          activeId={activeId}
        />
      )}
    </div>
  )
}

export default function NavBar() {
  const { currentView, setCurrentView } = useAppContext()

  function handleSelect(item) {
    setCurrentView({ id: item.id, category: item.id })
  }

  return (
    <nav className="navbar">
      {NAV_ITEMS.map(item => (
        <NavItem
          key={item.id}
          item={item}
          activeId={currentView.id}
          onSelect={handleSelect}
        />
      ))}
    </nav>
  )
}

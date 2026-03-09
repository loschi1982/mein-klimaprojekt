import { useState } from 'react'
import LoginForm from './admin/LoginForm'
import DataSourcesManager from './admin/DataSourcesManager'
import DatasetsOverview from './admin/DatasetsOverview'
import ReportEditor from './admin/ReportEditor'
import ReportScanner from './admin/ReportScanner'

function isAuthenticated() {
  return sessionStorage.getItem('admin_auth') === '1'
}

const TABS = [
  { id: 'data', label: 'Datenquellen' },
  { id: 'reports', label: 'KI-Berichte' },
  { id: 'scan', label: '🔍 Literatur-Scan' },
]

export default function AdminPanel() {
  const [authed, setAuthed] = useState(isAuthenticated)
  const [activeTab, setActiveTab] = useState('data')

  function handleLogout() {
    sessionStorage.removeItem('admin_auth')
    setAuthed(false)
  }

  if (!authed) {
    return <LoginForm onLogin={() => setAuthed(true)} />
  }

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <div>
          <h2 className="admin-title">Admin-Bereich</h2>
          <p className="admin-subtitle">Datenverwaltung und Systemkonfiguration</p>
        </div>
        <button className="btn btn--danger" onClick={handleLogout}>
          Abmelden
        </button>
      </div>

      <div className="admin-tabs">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`admin-tab-btn${activeTab === tab.id ? ' admin-tab-btn--active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'data' && (
        <>
          <DataSourcesManager />
          <DatasetsOverview />
        </>
      )}
      {activeTab === 'reports' && <ReportEditor />}
      {activeTab === 'scan' && <ReportScanner />}
    </div>
  )
}

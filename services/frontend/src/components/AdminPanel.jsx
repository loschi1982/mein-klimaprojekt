import { useState } from 'react'
import LoginForm from './admin/LoginForm'
import DataSourcesManager from './admin/DataSourcesManager'
import DatasetsOverview from './admin/DatasetsOverview'

function isAuthenticated() {
  return sessionStorage.getItem('admin_auth') === '1'
}

export default function AdminPanel() {
  const [authed, setAuthed] = useState(isAuthenticated)

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

      <DataSourcesManager />
      <DatasetsOverview />
    </div>
  )
}

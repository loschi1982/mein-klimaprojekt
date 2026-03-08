import { useState } from 'react'

const ADMIN_USER = 'admin'
const ADMIN_PASS = '1234'

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)

  function handleSubmit(e) {
    e.preventDefault()
    if (username === ADMIN_USER && password === ADMIN_PASS) {
      sessionStorage.setItem('admin_auth', '1')
      onLogin()
    } else {
      setError('Benutzername oder Passwort falsch.')
      setPassword('')
    }
  }

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="login-icon">🔒</div>
        <h2 className="login-title">Admin-Bereich</h2>
        <p className="login-subtitle">Anmeldung erforderlich</p>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Benutzername</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Passwort</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          {error && <p className="login-error">{error}</p>}

          <button type="submit" className="btn btn--primary btn--full">
            Anmelden
          </button>
        </form>
      </div>
    </div>
  )
}

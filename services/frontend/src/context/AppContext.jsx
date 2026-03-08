import { createContext, useContext, useState } from 'react'

const AppContext = createContext(null)

export const MIN_YEAR = 1880
export const MAX_YEAR = new Date().getFullYear()

export function AppProvider({ children }) {
  const [timeRange, setTimeRange] = useState([1960, MAX_YEAR])
  const [currentView, setCurrentView] = useState({
    id: 'co2_mauna_loa',
    category: 'climate',
  })

  return (
    <AppContext.Provider value={{ timeRange, setTimeRange, currentView, setCurrentView }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppContext() {
  return useContext(AppContext)
}

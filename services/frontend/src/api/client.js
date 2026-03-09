import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8001',
  headers: { 'Content-Type': 'application/json' },
})

// CO₂ (Mauna Loa, legacy)
export const fetchCo2Data = (from, to) =>
  api.get('/api/v1/analysis/co2', { params: { from_date: from, to_date: to } })
    .then(r => r.data.data.series)

// Generische Zeitreihe für beliebige Quellen
export const fetchSeries = (sourceId, from, to) =>
  api.get(`/api/v1/analysis/series/${sourceId}`, { params: { from_date: from, to_date: to } })
    .then(r => r.data.data)

// Temperaturen
export const fetchTemperature = (from, to) =>
  api.get('/api/v1/analysis/temperature', { params: { from_date: from, to_date: to } })
    .then(r => r.data.data)

export const fetchZonalTemperature = (year) =>
  api.get('/api/v1/analysis/temperature/zonal', { params: year ? { year } : {} })
    .then(r => r.data.data)

export const fetchCo2Annual = (fromYear, toYear) =>
  api.get('/api/v1/analysis/co2/annual', { params: { from_year: fromYear, to_year: toYear } })
    .then(r => r.data.data)

// Statistiken & Anomalien
export const fetchCo2Stats = () =>
  api.get('/api/v1/analysis/co2/stats').then(r => r.data.data)

export const fetchAnomalies = (threshold = 2.0) =>
  api.get('/api/v1/analysis/co2/anomalies', { params: { z_threshold: threshold } })
    .then(r => r.data.data)

// Simulation
export const fetchScenarios = () =>
  api.get('/api/v1/scenarios').then(r => r.data.data)

export const runSimulation = (scenario, years = 50, parameters = {}) =>
  api.post('/api/v1/simulate', { scenario, years, parameters }).then(r => r.data.data)

export const compareScenarios = (years = 50) =>
  api.post(`/api/v1/simulate/compare?years=${years}`).then(r => r.data.data)

// Admin
export const fetchSources = () =>
  api.get('/api/v1/sources').then(r => r.data.data)

export const ingestSource = (sourceId) =>
  api.post('/api/v1/ingest', { source: sourceId }).then(r => r.data.data)

export const fetchDatasets = () =>
  api.get('/api/v1/datasets').then(r => r.data.data)

export const fetchChartMeta = (chartId) =>
  api.get(`/api/v1/charts/${chartId}`).then(r => r.data.data)

export const explainDataPoint = (dataPoint, question) =>
  api.post('/api/v1/explain', { data_point: dataPoint, question })
    .then(r => r.data.data.explanation)

// KI-Chat
export const sendChatMessage = (message, context = {}, history = []) =>
  api.post('/api/v1/chat', { message, context, history }).then(r => r.data.data)

// KI-Bericht generieren
export const fetchAgentReport = (fromDate, toDate) =>
  api.get('/api/v1/analysis/co2/agent-report', { params: { from_date: fromDate, to_date: toDate } })
    .then(r => r.data.data)

// Admin: Berichte CRUD
export const fetchReports = () =>
  api.get('/api/v1/admin/reports').then(r => r.data.data)

export const saveReport = (title, content, sourceId = 'esrl_mauna_loa', tags = []) =>
  api.post('/api/v1/admin/reports', { title, content, source_id: sourceId, tags }).then(r => r.data.data)

export const getReport = (reportId) =>
  api.get(`/api/v1/admin/reports/${reportId}`).then(r => r.data.data)

export const updateReport = (reportId, title, content, sourceId, tags) =>
  api.put(`/api/v1/admin/reports/${reportId}`, { title, content, source_id: sourceId, tags }).then(r => r.data.data)

export const deleteReport = (reportId) =>
  api.delete(`/api/v1/admin/reports/${reportId}`).then(r => r.data.data)

export const fetchScanTopics = () =>
  api.get('/api/v1/admin/scan-topics').then(r => r.data.data.topics)

export const scanReports = (topic, maxPapers = 5) =>
  api.post('/api/v1/admin/scan-reports', { topic, max_papers: maxPapers }).then(r => r.data.data)

export const publishReport = (reportId, published) =>
  api.patch(`/api/v1/admin/reports/${reportId}/publish`, { published }).then(r => r.data.data)

// Öffentliche Berichte (kein Admin-Auth)
export const fetchPublishedReports = () =>
  api.get('/api/v1/reports').then(r => r.data.data)

export const fetchPublishedReport = (reportId) =>
  api.get(`/api/v1/reports/${reportId}`).then(r => r.data.data)

export default api

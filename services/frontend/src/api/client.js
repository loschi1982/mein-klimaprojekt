import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8001',
  headers: { 'Content-Type': 'application/json' },
})

export const fetchCo2Data = (from, to) =>
  api.get('/api/v1/analysis/co2', { params: { from_date: from, to_date: to } })
    .then(r => r.data.data.series)

export const fetchCo2Stats = () =>
  api.get('/api/v1/analysis/co2/stats').then(r => r.data.data)

export const fetchAnomalies = (threshold = 2.0) =>
  api.get('/api/v1/analysis/co2/anomalies', { params: { z_threshold: threshold } })
    .then(r => r.data.data)

export const fetchScenarios = () =>
  api.get('/api/v1/scenarios').then(r => r.data.data)

export const runSimulation = (scenario, years = 50, parameters = {}) =>
  api.post('/api/v1/simulate', { scenario, years, parameters }).then(r => r.data.data)

export const compareScenarios = (years = 50) =>
  api.post(`/api/v1/simulate/compare?years=${years}`).then(r => r.data.data)

export const fetchChartMeta = (chartId) =>
  api.get(`/api/v1/charts/${chartId}`).then(r => r.data.data)

export const explainDataPoint = (dataPoint, question) =>
  api.post('/api/v1/explain', { data_point: dataPoint, question })
    .then(r => r.data.data.explanation)

export default api

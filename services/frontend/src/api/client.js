import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

export const fetchCo2Data = (from, to) =>
  api.get('/api/v1/analysis/co2', { params: { from_date: from, to_date: to } })
    .then(r => r.data.data.series)

export const fetchChartMeta = (chartId) =>
  api.get(`/api/v1/charts/${chartId}`).then(r => r.data.data)

export const explainDataPoint = (dataPoint, question) =>
  api.post('/api/v1/explain', { data_point: dataPoint, question })
    .then(r => r.data.data.explanation)

export default api

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export function getConversations(status = '') {
  return api.get('/conversations', { params: { status } })
}

export function getConversation(id) {
  return api.get(`/conversations/${id}`)
}

export function extractSingle(convId) {
  return api.post('/extract', { conv_id: convId })
}

export function extractAll() {
  return api.post('/extract-all')
}

export function getResults() {
  return api.get('/results')
}

export function getResult(convId) {
  return api.get(`/results/${convId}`)
}

export function getStats() {
  return api.get('/stats')
}

export function getValidations() {
  return api.get('/validations')
}

export function validateField(convId, field, isCorrect) {
  return api.post('/validate', { conv_id: convId, field, is_correct: isCorrect })
}

export function getValidationSummary() {
  return api.get('/validate/summary')
}

export function validateBatch(validations) {
  return api.post('/validate/batch', { validations })
}

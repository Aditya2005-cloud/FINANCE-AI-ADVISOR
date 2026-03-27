async function readApiPayload(response) {
  const raw = await response.text()
  try {
    return JSON.parse(raw)
  } catch (_err) {
    const snippet = raw.slice(0, 180).replace(/\s+/g, ' ').trim()
    throw new Error(`Server returned non-JSON response (${response.status}): ${snippet}`)
  }
}

async function fetchJsonWithFallback(endpoints, options) {
  let lastError = null

  for (const endpoint of endpoints) {
    try {
      const response = await fetch(endpoint, options)
      const payload = await readApiPayload(response)

      if (!response.ok || payload.status !== 'success') {
        throw new Error(payload.message || payload.detail || 'Request failed')
      }

      return payload
    } catch (err) {
      lastError = err
    }
  }

  throw lastError || new Error('Request failed')
}

export async function analyzeFinancialUpload({ file, notes }) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('notes', notes || '')

  return fetchJsonWithFallback(['/api/ai/analyze', '/ml-api/api/ai/analyze'], {
    method: 'POST',
    body: formData,
  })
}

export async function askAdvisorQuestion({ sessionId, question }) {
  return fetchJsonWithFallback(['/api/ai/chat', '/ml-api/api/ai/chat'], {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      question,
    }),
  })
}

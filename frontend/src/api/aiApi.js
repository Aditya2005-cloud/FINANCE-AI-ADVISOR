async function readApiPayload(response) {
  const raw = await response.text()
  try {
    return JSON.parse(raw)
  } catch (_err) {
    const snippet = raw.slice(0, 180).replace(/\s+/g, ' ').trim()
    throw new Error(`Server returned non-JSON response (${response.status}): ${snippet}`)
  }
}

export async function analyzeFinancialUpload({ file, notes }) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('notes', notes || '')

  const response = await fetch('/api/ai/analyze', {
    method: 'POST',
    body: formData,
  })
  const payload = await readApiPayload(response)
  if (!response.ok || payload.status !== 'success') {
    throw new Error(payload.message || 'AI analysis failed')
  }
  return payload
}

export async function askAdvisorQuestion({ sessionId, question }) {
  const response = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      question,
    }),
  })
  const payload = await readApiPayload(response)
  if (!response.ok || payload.status !== 'success') {
    throw new Error(payload.message || 'AI chat failed')
  }
  return payload
}

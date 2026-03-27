import { useEffect, useMemo, useState } from 'react'
import { analyzeFinancialUpload, askAdvisorQuestion } from './api/aiApi'
import './App.css'

const initialForm = {
  applicantIncome: '',
  coapplicantIncome: '',
  loanAmount: '',
  creditHistory: '1',
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '-'
  }

  return date.toLocaleString()
}

async function readApiPayload(response) {
  const raw = await response.text()
  try {
    return JSON.parse(raw)
  } catch (_err) {
    const snippet = raw.slice(0, 180).replace(/\s+/g, ' ').trim()
    throw new Error(`Server returned non-JSON response (${response.status}): ${snippet}`)
  }
}

function App() {
  const [form, setForm] = useState(initialForm)
  const [prediction, setPrediction] = useState(null)
  const [stats, setStats] = useState(null)
  const [recentPredictions, setRecentPredictions] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingStats, setLoadingStats] = useState(false)
  const [predictionError, setPredictionError] = useState('')
  const [dashboardError, setDashboardError] = useState('')

  const [advisorFile, setAdvisorFile] = useState(null)
  const [advisorNotes, setAdvisorNotes] = useState('')
  const [advisorLoading, setAdvisorLoading] = useState(false)
  const [advisorError, setAdvisorError] = useState('')
  const [advisorWarning, setAdvisorWarning] = useState('')
  const [advisorSessionId, setAdvisorSessionId] = useState('')
  const [advisorGuidance, setAdvisorGuidance] = useState('')
  const [chatQuestion, setChatQuestion] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatHistory, setChatHistory] = useState([])

  const canSubmit = useMemo(() => {
    return (
      form.applicantIncome !== '' &&
      form.coapplicantIncome !== '' &&
      form.loanAmount !== ''
    )
  }, [form])

  async function fetchDashboard() {
    setLoadingStats(true)
    try {
      const response = await fetch('/api/predictions')
      const payload = await readApiPayload(response)

      if (!response.ok || payload.status !== 'success') {
        throw new Error(payload.message || 'Failed to fetch predictions')
      }

      setStats(payload.statistics)
      setRecentPredictions(payload.recent_predictions || [])
      setDashboardError('')
    } catch (err) {
      setDashboardError(err.message || 'Failed to load dashboard data')
    } finally {
      setLoadingStats(false)
    }
  }

  useEffect(() => {
    fetchDashboard()
  }, [])

  function handleInputChange(event) {
    const { name, value } = event.target
    setForm((previous) => ({ ...previous, [name]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setPredictionError('')

    try {
      const requestBody = JSON.stringify({
        ApplicantIncome: Number(form.applicantIncome),
        CoapplicantIncome: Number(form.coapplicantIncome),
        LoanAmount: Number(form.loanAmount),
        Credit_History: Number(form.creditHistory),
      })
      const predictionEndpoints = ['/ml-api/api/v1/predict', '/api/predict']

      let result = null
      let lastError = null

      for (const endpoint of predictionEndpoints) {
        try {
          const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: requestBody,
          })

          const payload = await readApiPayload(response)
          const candidate = payload.data || payload

          if (!response.ok || payload.status !== 'success' || !candidate?.prediction) {
            throw new Error(payload.message || payload.detail || 'Prediction request failed')
          }

          result = candidate
          break
        } catch (err) {
          lastError = err
        }
      }

      if (!result) {
        throw lastError || new Error('Prediction request failed')
      }

      setPrediction(result)
      fetchDashboard()
    } catch (err) {
      setPredictionError(err.message || 'Prediction request failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleAnalyzeFinancials(event) {
    event.preventDefault()
    setAdvisorError('')
    setAdvisorWarning('')

    if (!advisorFile) {
      setAdvisorError('Please upload a financial file first.')
      return
    }

    setAdvisorLoading(true)
    try {
      const payload = await analyzeFinancialUpload({ file: advisorFile, notes: advisorNotes })
      setAdvisorGuidance(payload.guidance || '')
      setAdvisorSessionId(payload.session_id || '')
      setAdvisorWarning(payload.provider_warning || '')
      setChatHistory([])
    } catch (err) {
      setAdvisorError(err.message || 'Failed to analyze uploaded file')
    } finally {
      setAdvisorLoading(false)
    }
  }

  async function handleAskAdvisor(event) {
    event.preventDefault()
    setAdvisorError('')

    if (!advisorSessionId) {
      setAdvisorError('Run analysis first to start an advisor session.')
      return
    }
    if (!chatQuestion.trim()) {
      setAdvisorError('Enter a follow-up question.')
      return
    }

    const question = chatQuestion.trim()
    setChatLoading(true)
    try {
      const payload = await askAdvisorQuestion({
        sessionId: advisorSessionId,
        question,
      })
      setChatHistory((prev) => [...prev, { question, answer: payload.answer || '' }])
      setAdvisorWarning(payload.provider_warning || '')
      setChatQuestion('')
    } catch (err) {
      setAdvisorError(err.message || 'Failed to fetch advisor response')
    } finally {
      setChatLoading(false)
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <p className="eyebrow">Finance AI Advisor</p>
        <h1>Loan + Financial Upload AI Advisor</h1>
        <p className="subhead">
          Upload your financial file to receive guidelines, then continue Q&A in the same advisor
          session.
        </p>
      </header>

      <section className="panel form-panel">
        <h2>Run Prediction</h2>
        <form onSubmit={handleSubmit} className="grid-form">
          <label>
            Applicant Income
            <input
              type="number"
              min="0"
              step="1"
              name="applicantIncome"
              value={form.applicantIncome}
              onChange={handleInputChange}
              placeholder="e.g. 5000"
              required
            />
          </label>

          <label>
            Coapplicant Income
            <input
              type="number"
              min="0"
              step="1"
              name="coapplicantIncome"
              value={form.coapplicantIncome}
              onChange={handleInputChange}
              placeholder="e.g. 1200"
              required
            />
          </label>

          <label>
            Loan Amount
            <input
              type="number"
              min="0"
              step="1"
              name="loanAmount"
              value={form.loanAmount}
              onChange={handleInputChange}
              placeholder="e.g. 150"
              required
            />
          </label>

          <label>
            Credit History
            <select name="creditHistory" value={form.creditHistory} onChange={handleInputChange}>
              <option value="1">Good (1)</option>
              <option value="0">Poor (0)</option>
            </select>
          </label>

          <button type="submit" disabled={!canSubmit || loading}>
            {loading ? 'Predicting...' : 'Predict Loan Status'}
          </button>
        </form>

        {prediction && (
          <div className={`result ${prediction.prediction === 'Approved' ? 'ok' : 'bad'}`}>
            <strong>Result: {prediction.prediction}</strong>
            {typeof prediction.probability_approved === 'number' && (
              <span>
                Probability Approved: {(prediction.probability_approved * 100).toFixed(2)}%
              </span>
            )}
          </div>
        )}

        {predictionError && <p className="error">{predictionError}</p>}
      </section>

      <section className="panel">
        <h2>AI Financial Upload Advisor</h2>
        <form onSubmit={handleAnalyzeFinancials} className="advisor-form">
          <label>
            Upload financial data (.csv, .txt, .json, .xlsx)
            <input
              type="file"
              accept=".csv,.txt,.json,.tsv,.xlsx,.xls"
              onChange={(event) => setAdvisorFile(event.target.files?.[0] || null)}
              required
            />
          </label>
          <label>
            Extra context for advisor (optional)
            <textarea
              rows="5"
              placeholder="Example: irregular income in the last 3 months, planning to reduce debt..."
              value={advisorNotes}
              onChange={(event) => setAdvisorNotes(event.target.value)}
            />
          </label>
          <button type="submit" disabled={advisorLoading}>
            {advisorLoading ? 'Analyzing...' : 'Analyze Upload'}
          </button>
        </form>

        {advisorGuidance && (
          <div className="advisor-output">
            <h3>Guidelines and Advice</h3>
            <pre>{advisorGuidance}</pre>
          </div>
        )}

        {advisorSessionId && (
          <form onSubmit={handleAskAdvisor} className="advisor-chat">
            <h3>Ask Follow-up Questions (Same Session)</h3>
            <textarea
              rows="3"
              placeholder="Ask anything about the advice, risks, or next steps..."
              value={chatQuestion}
              onChange={(event) => setChatQuestion(event.target.value)}
            />
            <button type="submit" disabled={chatLoading}>
              {chatLoading ? 'Thinking...' : 'Ask Advisor'}
            </button>
          </form>
        )}

        {chatHistory.length > 0 && (
          <div className="chat-history">
            {chatHistory.map((item, index) => (
              <article key={`${item.question}-${index}`}>
                <p>
                  <strong>You:</strong> {item.question}
                </p>
                <p>
                  <strong>Advisor:</strong> {item.answer}
                </p>
              </article>
            ))}
          </div>
        )}

        {advisorWarning && <p className="warning">{advisorWarning}</p>}
        {advisorError && <p className="error">{advisorError}</p>}
      </section>

      <section className="panel">
        <h2>Prediction Stats</h2>
        {dashboardError && <p className="error">{dashboardError}</p>}
        {loadingStats && !stats ? (
          <p>Loading analytics...</p>
        ) : stats ? (
          <div className="stats-grid">
            <article>
              <span>Total</span>
              <strong>{stats.total_predictions}</strong>
            </article>
            <article>
              <span>Approved</span>
              <strong>{stats.approved}</strong>
            </article>
            <article>
              <span>Rejected</span>
              <strong>{stats.rejected}</strong>
            </article>
            <article>
              <span>Approval Rate</span>
              <strong>{stats.approval_rate_percent}%</strong>
            </article>
          </div>
        ) : (
          <p>No statistics available yet.</p>
        )}
      </section>

      <section className="panel">
        <h2>Recent Predictions</h2>
        {recentPredictions.length === 0 ? (
          <p>No predictions logged yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Applicant</th>
                  <th>Coapplicant</th>
                  <th>Loan</th>
                  <th>Credit</th>
                  <th>Decision</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {recentPredictions.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>{item.applicant_income}</td>
                    <td>{item.coapplicant_income}</td>
                    <td>{item.loan_amount}</td>
                    <td>{item.credit_history}</td>
                    <td>{item.prediction}</td>
                    <td>{formatDateTime(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  )
}

export default App

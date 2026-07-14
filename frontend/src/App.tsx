import { useEffect, useState } from 'react'
import {
  fetchJson,
  type FlowPayload,
  type HealthPayload,
} from './api'
import { MetricsTable } from './components/MetricsTable'
import { PlotlyChart } from './components/PlotlyChart'
import './App.css'

type SectionState = {
  loading: boolean
  error: string | null
  data: FlowPayload | null
}

const emptySection: SectionState = {
  loading: true,
  error: null,
  data: null,
}

function App() {
  const [health, setHealth] = useState<HealthPayload | null>(null)
  const [inbound, setInbound] = useState<SectionState>(emptySection)
  const [outbound, setOutbound] = useState<SectionState>(emptySection)
  const [refreshing, setRefreshing] = useState(false)

  async function loadAll() {
    setInbound(emptySection)
    setOutbound(emptySection)
    try {
      const h = await fetchJson<HealthPayload>('/api/health')
      setHealth(h)
    } catch (err) {
      setHealth(null)
      console.error(err)
    }

    try {
      const data = await fetchJson<FlowPayload>('/api/inbound')
      setInbound({ loading: false, error: null, data })
    } catch (err) {
      setInbound({
        loading: false,
        error: err instanceof Error ? err.message : String(err),
        data: null,
      })
    }

    try {
      const data = await fetchJson<FlowPayload>('/api/outbound')
      setOutbound({ loading: false, error: null, data })
    } catch (err) {
      setOutbound({
        loading: false,
        error: err instanceof Error ? err.message : String(err),
        data: null,
      })
    }
  }

  useEffect(() => {
    void loadAll()
  }, [])

  async function onRefresh() {
    setRefreshing(true)
    try {
      await fetch('/api/refresh', { method: 'POST' })
    } catch (err) {
      console.error(err)
    }
    await loadAll()
    setRefreshing(false)
  }

  const monthHeaders = inbound.data?.month_labels ?? outbound.data?.month_labels ?? []

  return (
    <div className="page">
      <header className="header">
        <div>
          <p className="eyebrow">IBOB</p>
          <h1>Passenger Traffic Dashboard</h1>
          <p className="meta">
            {health?.source ?? 'API offline — start uvicorn on :8000'}
            {health?.daily_in_rows
              ? ` · ${health.daily_in_rows.toLocaleString()} daily inbound rows`
              : null}
          </p>
        </div>
        <button type="button" onClick={() => void onRefresh()} disabled={refreshing}>
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </header>

      <section id="inbound" className="section">
        <h2>Inbound Tourist Arrivals</h2>
        <FlowSection
          state={inbound}
          monthHeaders={[''].concat(monthHeaders)}
        />
      </section>

      <section id="outbound" className="section">
        <h2>Outbound HK Resident Departures</h2>
        <FlowSection
          state={outbound}
          monthHeaders={[''].concat(monthHeaders)}
        />
      </section>

      <footer className="footer">
        Phase 1 — FastAPI + React. International & holiday sections next.
      </footer>
    </div>
  )
}

function FlowSection({
  state,
  monthHeaders,
}: {
  state: SectionState
  monthHeaders: string[]
}) {
  if (state.loading) return <p className="muted">Loading…</p>
  if (state.error) return <p className="error">{state.error}</p>
  if (!state.data) return <p className="muted">No data</p>

  const { data } = state
  return (
    <>
      <PlotlyChart figure={data.figure} />
      <div className="tables">
        <MetricsTable
          title="YoY Growth"
          headers={monthHeaders}
          rows={data.yoy_rows}
        />
        <MetricsTable
          title="Recovery vs 2018"
          headers={monthHeaders}
          rows={data.recovery_rows}
        />
      </div>
    </>
  )
}

export default App

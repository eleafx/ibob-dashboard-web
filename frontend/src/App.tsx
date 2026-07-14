import { useEffect, useState } from 'react'
import {
  fetchJson,
  type FlowPayload,
  type HealthPayload,
  type InternationalPayload,
} from './api'
import { HolidaySection } from './components/HolidaySection'
import { MetricsTable } from './components/MetricsTable'
import { MonthlyYoyTable } from './components/MonthlyYoyTable'
import { PlotlyChart } from './components/PlotlyChart'
import { PptSummaryTable } from './components/PptSummaryTable'
import './App.css'

type SectionState<T> = {
  loading: boolean
  error: string | null
  data: T | null
}

const emptySection = <T,>(): SectionState<T> => ({
  loading: true,
  error: null,
  data: null,
})

type IntlView = 'ytd' | 'monthly'

function App() {
  const [health, setHealth] = useState<HealthPayload | null>(null)
  const [inbound, setInbound] = useState(emptySection<FlowPayload>())
  const [outbound, setOutbound] = useState(emptySection<FlowPayload>())
  const [international, setInternational] = useState(
    emptySection<InternationalPayload>(),
  )
  const [intlView, setIntlView] = useState<IntlView>('ytd')
  const [refreshing, setRefreshing] = useState(false)
  const [refreshToken, setRefreshToken] = useState(0)

  async function loadAll() {
    setInbound(emptySection())
    setOutbound(emptySection())
    setInternational(emptySection())
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

    try {
      const data = await fetchJson<InternationalPayload>('/api/international')
      setInternational({ loading: false, error: null, data })
    } catch (err) {
      setInternational({
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
    setRefreshToken((n) => n + 1)
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

      <nav className="toc">
        <a href="#inbound">Inbound</a>
        <a href="#international">International</a>
        <a href="#holiday">Holiday</a>
        <a href="#outbound">Outbound</a>
      </nav>

      <section id="inbound" className="section">
        <h2>Inbound Tourist Arrivals</h2>
        <FlowSection state={inbound} monthHeaders={[''].concat(monthHeaders)} />
      </section>

      <section id="international" className="section">
        <h2>International Visitor Arrivals</h2>
        <InternationalSection
          state={international}
          view={intlView}
          onViewChange={setIntlView}
        />
      </section>

      <section id="holiday" className="section">
        <h2>Holiday Period Analysis</h2>
        <HolidaySection refreshToken={refreshToken} />
      </section>

      <section id="outbound" className="section">
        <h2>Outbound HK Resident Departures</h2>
        <FlowSection state={outbound} monthHeaders={[''].concat(monthHeaders)} />
      </section>

      <footer className="footer">
        Phase 3 — Holiday analysis. Deploy / cutover next.
      </footer>
    </div>
  )
}

function FlowSection({
  state,
  monthHeaders,
}: {
  state: SectionState<FlowPayload>
  monthHeaders: string[]
}) {
  if (state.loading) return <p className="muted">Loading…</p>
  if (state.error) return <p className="error">{state.error}</p>
  if (!state.data) return <p className="muted">No data</p>

  const { data } = state
  return (
    <>
      <PlotlyChart figure={data.figure} />
      {data.summary_figure ? (
        <PlotlyChart figure={data.summary_figure} className="summary-figure" />
      ) : (
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
      )}
    </>
  )
}

function InternationalSection({
  state,
  view,
  onViewChange,
}: {
  state: SectionState<InternationalPayload>
  view: IntlView
  onViewChange: (v: IntlView) => void
}) {
  if (state.loading) return <p className="muted">Loading…</p>
  if (state.error) return <p className="error">{state.error}</p>
  if (!state.data) return <p className="muted">No data</p>

  const data = state.data
  const period = data.ppt_summary.meta?.period_label ?? `YTD ${data.curr_year}`

  return (
    <>
      <p className="meta">
        {data.meta} · {data.rows.toLocaleString()} rows · through{' '}
        {data.curr_year}-{String(data.curr_month).padStart(2, '0')}
      </p>

      {data.monthly_figure ? <PlotlyChart figure={data.monthly_figure} /> : null}

      <div className="view-toggle" role="group" aria-label="International view">
        <button
          type="button"
          className={view === 'ytd' ? 'active' : undefined}
          onClick={() => onViewChange('ytd')}
        >
          YTD Summary
        </button>
        <button
          type="button"
          className={view === 'monthly' ? 'active' : undefined}
          onClick={() => onViewChange('monthly')}
        >
          Monthly Detail
        </button>
      </div>

      {view === 'ytd' ? (
        <>
          <h3 className="subhead">
            Visitor Arrivals Summary (Daily Average) — {period}
          </h3>
          {data.ppt_summary.rows.length ? (
            <PptSummaryTable data={data.ppt_summary} />
          ) : (
            <p className="muted">Not enough data for PPT summary.</p>
          )}
        </>
      ) : (
        <>
          {data.yoy_figure ? <PlotlyChart figure={data.yoy_figure} /> : null}
          {data.monthly_yoy_table ? (
            <>
              <h3 className="subhead">
                Monthly YoY Breakdown by Market — {data.monthly_yoy_table.curr_year} vs{' '}
                {data.monthly_yoy_table.prev_year} (daily avg)
              </h3>
              <MonthlyYoyTable data={data.monthly_yoy_table} />
            </>
          ) : (
            <p className="muted">No prior-year data available for YoY comparison.</p>
          )}
        </>
      )}

      <p className="caption">Source: HKTB PartnerNet (COR Arrivals).</p>
    </>
  )
}

export default App

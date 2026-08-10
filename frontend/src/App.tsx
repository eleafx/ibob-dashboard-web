import { useCallback, useEffect, useRef, useState } from 'react'
import {
  apiUrl,
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
type InboundMode = 'daily_avg' | 'monthly'

function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}

function Loading() {
  return (
    <div className="loading-wrap">
      <Spinner /> Loading…
    </div>
  )
}

function ErrorBlock({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="error-wrap">
      <p className="error">{message}</p>
      <button type="button" className="retry-btn" onClick={onRetry}>
        Retry
      </button>
    </div>
  )
}

function App() {
  const [health, setHealth] = useState<HealthPayload | null>(null)
  const [inbound, setInbound] = useState(emptySection<FlowPayload>())
  const [outbound, setOutbound] = useState(emptySection<FlowPayload>())
  const [international, setInternational] = useState(
    emptySection<InternationalPayload>(),
  )
  const [intlView, setIntlView] = useState<IntlView>('ytd')
  const [inboundMode, setInboundMode] = useState<InboundMode>('daily_avg')
  const [refreshing, setRefreshing] = useState(false)
  const [fetchingGov, setFetchingGov] = useState(false)
  const [refreshToken, setRefreshToken] = useState(0)
  const [showScrollTop, setShowScrollTop] = useState(false)
  const pageRef = useRef<HTMLDivElement>(null)

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
      const data = await fetchJson<FlowPayload>(`/api/inbound?mode=${inboundMode}`)
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
      const data = await fetchJson<InternationalPayload>(`/api/international?mode=${inboundMode}`)
      setInternational({ loading: false, error: null, data })
    } catch (err) {
      setInternational({
        loading: false,
        error: err instanceof Error ? err.message : String(err),
        data: null,
      })
    }
  }

  const retryLoadAll = useCallback(() => {
    void loadAll()
  }, [])

  useEffect(() => {
    void loadAll()
  }, [inboundMode])

  useEffect(() => {
    function onScroll() {
      setShowScrollTop(window.scrollY > 400)
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function onRefresh() {
    setRefreshing(true)
    try {
      await fetch(apiUrl('/api/refresh'), { method: 'POST' })
    } catch (err) {
      console.error(err)
    }
    await loadAll()
    setRefreshToken((n) => n + 1)
    setRefreshing(false)
  }

  async function onRefetchFromGov() {
    setFetchingGov(true)
    try {
      await fetch(apiUrl('/api/refresh?from_gov=true'), { method: 'POST' })
    } catch (err) {
      console.error(err)
    }
    await loadAll()
    setRefreshToken((n) => n + 1)
    setFetchingGov(false)
  }

  const monthHeaders = inbound.data?.month_labels ?? outbound.data?.month_labels ?? []

  return (
    <div className="page" ref={pageRef}>
      <header className="header">
        <div>
          <p className="eyebrow">IBOB</p>
          <h1>Passenger Traffic Dashboard</h1>
          {health ? (
            <p className="meta">
              Last updated: {health.last_updated_file ?? 'unknown'}
            </p>
          ) : (
            <p className="meta">API offline — start uvicorn on :8000</p>
          )}
        </div>
        <div className="header-actions">
          <button type="button" onClick={() => void onRefresh()} disabled={refreshing || fetchingGov}>
            {refreshing ? 'Refreshing…' : 'Refresh'}
          </button>
          <button
            type="button"
            className="ghost"
            onClick={() => void onRefetchFromGov()}
            disabled={refreshing || fetchingGov}
          >
            {fetchingGov ? 'Downloading from IMMD…' : 'Refetch from source'}
          </button>
        </div>
      </header>

      <nav className="toc" aria-label="Section navigation">
        <a href="#inbound">Inbound</a>
        <a href="#outbound">Outbound</a>
        <a href="#holiday">Holiday</a>
      </nav>

      <main>
        <section id="inbound" className="section">
          <div className="section-header-row">
            <h2>Inbound Tourist Arrivals</h2>
            <div className="mode-toggle" role="group" aria-label="Data mode">
              <button
                type="button"
                className={inboundMode === 'daily_avg' ? 'active' : undefined}
                onClick={() => setInboundMode('daily_avg')}
              >
                Daily Avg
              </button>
              <button
                type="button"
                className={inboundMode === 'monthly' ? 'active' : undefined}
                onClick={() => setInboundMode('monthly')}
              >
                Monthly Total
              </button>
            </div>
          </div>
          <FlowSection state={inbound} monthHeaders={[''].concat(monthHeaders)} onRetry={retryLoadAll} showRecovery mode={inboundMode} />
          <InternationalSection
            state={international}
            view={intlView}
            onViewChange={setIntlView}
            onRetry={retryLoadAll}
            mode={inboundMode}
          />
        </section>

        <section id="outbound" className="section">
          <h2>Outbound HK Resident Departures</h2>
          <FlowSection state={outbound} monthHeaders={[''].concat(monthHeaders)} onRetry={retryLoadAll} />
        </section>

        <section id="holiday" className="section">
          <h2>Holiday Period Analysis</h2>
          <HolidaySection refreshToken={refreshToken} />
        </section>
      </main>

    <button
        type="button"
        className={`scroll-top${showScrollTop ? ' visible' : ''}`}
        onClick={scrollToTop}
        aria-label="Scroll to top"
      >
        ↑
      </button>
    </div>
  )
}

function FlowSection({
  state,
  monthHeaders,
  onRetry,
  showRecovery = false,
  mode = 'daily_avg',
}: {
  state: SectionState<FlowPayload>
  monthHeaders: string[]
  onRetry: () => void
  showRecovery?: boolean
  mode?: InboundMode
}) {
  if (state.loading) return <Loading />
  if (state.error) return <ErrorBlock message={state.error} onRetry={onRetry} />
  if (!state.data) return <p className="muted">No data</p>

  const { data } = state
  const unitLabel = mode === 'monthly' ? 'monthly total' : 'daily avg'
  return (
    <>
      <PlotlyChart figure={data.figure} />
      {data.summary_figure ? (
        <PlotlyChart figure={data.summary_figure} className="summary-figure" />
      ) : (
        <div className="tables">
          <MetricsTable
            title={`YoY Growth (${unitLabel})`}
            headers={monthHeaders}
            rows={data.yoy_rows}
          />
          {showRecovery ? (
            <MetricsTable
              title={`Recovery vs 2018 (${unitLabel})`}
              headers={monthHeaders}
              rows={data.recovery_rows}
            />
          ) : null}
        </div>
      )}
      <p className="caption">
        Source:{' '}
        <a
          href="https://www.immd.gov.hk/opendata/eng/transport/immigration_clearance/statistics_on_daily_passenger_traffic.csv"
          target="_blank"
          rel="noopener noreferrer"
        >
          Immigration Department Open Data
        </a>
      </p>
    </>
  )
}

function InternationalSection({
  state,
  view,
  onViewChange,
  onRetry,
  mode = 'daily_avg',
}: {
  state: SectionState<InternationalPayload>
  view: IntlView
  onViewChange: (v: IntlView) => void
  onRetry: () => void
  mode?: InboundMode
}) {
  if (state.loading) return <Loading />
  if (state.error) return <ErrorBlock message={state.error} onRetry={onRetry} />
  if (!state.data) return <p className="muted">No data</p>

  const data = state.data
  const period = data.ppt_summary.meta?.period_label ?? `YTD ${data.curr_year}`
  const unitLabel = mode === 'monthly' ? 'Monthly Total' : 'Daily Average'

  return (
    <>
      {data.monthly_figure ? <PlotlyChart figure={data.monthly_figure} /> : null}

      <div className="view-toggle" role="group" aria-label="Overall arrivals view">
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
            Overall Visitor Arrivals Summary ({unitLabel}) — {period}
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
                {data.monthly_yoy_table.prev_year} ({unitLabel.toLowerCase()})
              </h3>
              <MonthlyYoyTable data={data.monthly_yoy_table} />
            </>
          ) : (
            <p className="muted">No prior-year data available for YoY comparison.</p>
          )}
        </>
      )}

      <p className="caption">
        Source:{' '}
        <a
          href="https://partnernet.hktb.com/en/research_statistics/tourism_performance/index.html"
          target="_blank"
          rel="noopener noreferrer"
        >
          HKTB PartnerNet (COR Arrivals)
        </a>
      </p>
    </>
  )
}

export default App

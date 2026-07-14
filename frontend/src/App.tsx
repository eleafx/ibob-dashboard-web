import { useCallback, useEffect, useRef, useState } from 'react'
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

  const retryLoadAll = useCallback(() => {
    void loadAll()
  }, [])

  useEffect(() => {
    void loadAll()
  }, [])

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
      await fetch('/api/refresh', { method: 'POST' })
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
      await fetch('/api/refresh?from_gov=true', { method: 'POST' })
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
        <a href="#international">International</a>
        <a href="#holiday">Holiday</a>
        <a href="#outbound">Outbound</a>
      </nav>

      <main>
        <section id="inbound" className="section">
          <h2>Inbound Tourist Arrivals</h2>
          <FlowSection state={inbound} monthHeaders={[''].concat(monthHeaders)} onRetry={retryLoadAll} />
        </section>

        <section id="international" className="section">
          <h2>International Visitor Arrivals</h2>
          <InternationalSection
            state={international}
            view={intlView}
            onViewChange={setIntlView}
            onRetry={retryLoadAll}
          />
        </section>

        <section id="holiday" className="section">
          <h2>Holiday Period Analysis</h2>
          <HolidaySection refreshToken={refreshToken} />
        </section>

        <section id="outbound" className="section">
          <h2>Outbound HK Resident Departures</h2>
          <FlowSection state={outbound} monthHeaders={[''].concat(monthHeaders)} onRetry={retryLoadAll} />
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
}: {
  state: SectionState<FlowPayload>
  monthHeaders: string[]
  onRetry: () => void
}) {
  if (state.loading) return <Loading />
  if (state.error) return <ErrorBlock message={state.error} onRetry={onRetry} />
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
}: {
  state: SectionState<InternationalPayload>
  view: IntlView
  onViewChange: (v: IntlView) => void
  onRetry: () => void
}) {
  if (state.loading) return <Loading />
  if (state.error) return <ErrorBlock message={state.error} onRetry={onRetry} />
  if (!state.data) return <p className="muted">No data</p>

  const data = state.data
  const period = data.ppt_summary.meta?.period_label ?? `YTD ${data.curr_year}`

  return (
    <>
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

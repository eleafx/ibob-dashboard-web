import { useEffect, useMemo, useState } from 'react'
import {
  fetchJson,
  holidayQuery,
  type HolidayOptions,
  type HolidayPayload,
} from '../api'
import { PlotlyChart } from './PlotlyChart'

type HolidayView = 'official' | 'al'
type VolumeBasis = 'total' | 'avg'

type Props = {
  refreshToken: number
}

export function HolidaySection({ refreshToken }: Props) {
  const [options, setOptions] = useState<HolidayOptions | null>(null)
  const [context, setContext] = useState('Mainland')
  const [direction, setDirection] = useState('inbound')
  const [segment, setSegment] = useState('All tourists')
  const [holiday, setHoliday] = useState('CNY')
  const [view, setView] = useState<HolidayView>('official')
  const [volumeBasis, setVolumeBasis] = useState<VolumeBasis>('total')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<HolidayPayload | null>(null)

  const region = context === 'HK' ? 'HK' : 'CN'
  const holidayKeys = useMemo(() => {
    if (!options) return ['CNY']
    return options.holidays_by_region[region] ?? ['CNY']
  }, [options, region])

  const segments = useMemo(() => {
    if (!options) return []
    return direction === 'inbound'
      ? options.inbound_segments
      : options.outbound_segments
  }, [options, direction])

  useEffect(() => {
    void fetchJson<HolidayOptions>('/api/holiday/options')
      .then(setOptions)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  useEffect(() => {
    const defaultDir = context === 'HK' ? 'outbound' : 'inbound'
    setDirection(defaultDir)
    setSegment(defaultDir === 'inbound' ? 'All tourists' : 'HK Residents')
    setView('official')
    const keys = options?.holidays_by_region[context === 'HK' ? 'HK' : 'CN']
    if (keys?.length) setHoliday(keys[0])
  }, [context, options])

  useEffect(() => {
    if (!segments.includes(segment) && segments.length) {
      setSegment(segments[direction === 'outbound' ? 1 : 0] ?? segments[0])
    }
  }, [segments, segment, direction])

  useEffect(() => {
    if (!holidayKeys.includes(holiday) && holidayKeys.length) {
      setHoliday(holidayKeys[0])
    }
  }, [holidayKeys, holiday])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      const variant =
        view === 'official' ? 'Official Days' : 'Extended Leave Days'
      try {
        const payload = await fetchJson<HolidayPayload>(
          holidayQuery({
            context,
            holiday,
            direction,
            segment,
            variant,
          }),
        )
        if (!cancelled) {
          setData(payload)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setData(null)
          setError(err instanceof Error ? err.message : String(err))
          setLoading(false)
        }
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [context, holiday, direction, segment, view, refreshToken])

  return (
    <div className="holiday">
      <div className="holiday-controls">
        <fieldset>
          <legend>Calendar</legend>
          <div className="view-toggle">
            {(['Mainland', 'HK'] as const).map((c) => (
              <button
                key={c}
                type="button"
                className={context === c ? 'active' : undefined}
                onClick={() => setContext(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend>Direction</legend>
          <div className="view-toggle">
            {(['inbound', 'outbound'] as const).map((d) => (
              <button
                key={d}
                type="button"
                className={direction === d ? 'active' : undefined}
                onClick={() => setDirection(d)}
              >
                {d === 'inbound' ? 'Inbound' : 'Outbound'}
              </button>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend>Segment</legend>
          <div className="view-toggle wrap">
            {segments.map((s) => (
              <button
                key={s}
                type="button"
                className={segment === s ? 'active' : undefined}
                onClick={() => setSegment(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </fieldset>

        <label className="holiday-select">
          Holiday
          <select value={holiday} onChange={(e) => setHoliday(e.target.value)}>
            {holidayKeys.map((k) => (
              <option key={k} value={k}>
                {options?.holiday_display[k] ?? k}
              </option>
            ))}
          </select>
        </label>
      </div>

      {data?.tracker?.length ? (
        <div className="tracker">
          <h3 className="subhead">Holiday Proximity Tracker</h3>
          {data.tracker.map((row) => (
            <div key={row.year} className="tracker-year">
              <p className="tracker-label">
                <strong>Year {row.year}</strong> · {row.label}
              </p>
              <div className="cal-container">
                {row.days.map((d) => (
                  <div key={d.date} className={`cal-day is-${d.kind}`}>
                    <div className="day-header">{d.weekday}</div>
                    <div className="day-num">{d.day}</div>
                    <div className="day-month">{d.month}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          <p className="cal-legend">
            <span className="leg-official">■</span> Gazetted Holiday ·{' '}
            <span className="leg-weekend">■</span> Weekend ·{' '}
            <span className="leg-leave">■</span> AL bridge day
          </p>
        </div>
      ) : null}

      <div className="view-toggle" role="tablist" aria-label="Holiday variant">
        <button
          type="button"
          className={view === 'official' ? 'active' : undefined}
          onClick={() => setView('official')}
        >
          Official View
        </button>
        <button
          type="button"
          className={view === 'al' ? 'active' : undefined}
          onClick={() => setView('al')}
          disabled={region === 'CN'}
          title={
            region === 'CN'
              ? 'Annual Leave view is not applicable for Mainland holidays'
              : undefined
          }
        >
          Annual Leave View
        </button>
      </div>

      {region === 'CN' && view === 'al' ? (
        <p className="muted">
          Annual Leave view is not applicable for Mainland holidays
          (state-mandated holiday blocks only).
        </p>
      ) : null}

      {loading ? <p className="muted">Loading holiday data…</p> : null}
      {error ? <p className="error">{error}</p> : null}

      {!loading && data && !data.ok ? (
        <p className="muted">{data.message ?? 'No holiday data'}</p>
      ) : null}

      {!loading && data?.ok ? (
        <>
          {data.al_warnings?.length ? (
            <p className="warn">
              Years using Official window in this view (no separate AL bridge):{' '}
              {data.al_warnings.join(' · ')}
            </p>
          ) : null}

          {data.overview_figure ? (
            <PlotlyChart figure={data.overview_figure} />
          ) : null}

          <div className="holiday-panels">
            <div>
              <h3 className="subhead">
                Daily {data.flow_label} by day — {data.variant}
              </h3>
              {data.daily_figure ? (
                <PlotlyChart figure={data.daily_figure} />
              ) : null}
            </div>
            <div>
              <h3 className="subhead">
                {data.flow_label} — {data.variant}
              </h3>
              <div className="view-toggle compact">
                <button
                  type="button"
                  className={volumeBasis === 'total' ? 'active' : undefined}
                  onClick={() => setVolumeBasis('total')}
                >
                  Period total
                </button>
                <button
                  type="button"
                  className={volumeBasis === 'avg' ? 'active' : undefined}
                  onClick={() => setVolumeBasis('avg')}
                >
                  Daily average
                </button>
              </div>
              {volumeBasis === 'total' && data.bar_total_figure ? (
                <PlotlyChart figure={data.bar_total_figure} />
              ) : null}
              {volumeBasis === 'avg' && data.bar_avg_figure ? (
                <PlotlyChart figure={data.bar_avg_figure} />
              ) : null}
            </div>
          </div>

          {data.cp_figure ? (
            <>
              <h3 className="subhead">
                Avg. Daily {data.flow_label} by Control Point —{' '}
                {data.holiday_label} ({data.variant})
              </h3>
              <PlotlyChart figure={data.cp_figure} />
            </>
          ) : (
            <p className="caption">
              No control-point breakdown available for this period.
            </p>
          )}

          {data.cp_table ? (
            <div className="ppt-table-wrap">
              <h3 className="subhead">
                Total {data.flow_label} by Control Point — {data.holiday_label} (
                {data.variant})
              </h3>
              <div className="table-scroll">
                <table className="ppt-table">
                  <thead>
                    <tr>
                      {data.cp_table.columns.map((c) => (
                        <th key={c}>{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.cp_table.rows.map((row) => (
                      <tr key={String(row['Control Point'])}>
                        {data.cp_table!.columns.map((c) => {
                          const val = row[c]
                          const isYoy = data.cp_table!.yoy_columns.includes(c)
                          const color = isYoy
                            ? String(row[`${c}__color`] ?? '#111')
                            : undefined
                          const display =
                            typeof val === 'number'
                              ? val.toLocaleString()
                              : (val ?? '—')
                          return (
                            <td
                              key={c}
                              className={
                                c === 'Control Point' ? 'col-market' : undefined
                              }
                              style={color ? { color } : undefined}
                            >
                              {display}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

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
      ) : null}
    </div>
  )
}

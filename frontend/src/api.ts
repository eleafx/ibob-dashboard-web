export type MetricRow = {
  label: string
  values: string[]
}

export type PlotlyFigure = {
  data: Record<string, unknown>[]
  layout?: Record<string, unknown>
}

export type FlowPayload = {
  flow: string
  meta: string
  display_years: number[]
  month_labels: string[]
  series: Record<string, (number | null)[]>
  figure: PlotlyFigure
  summary_figure?: PlotlyFigure
  yoy_rows: MetricRow[]
  recovery_rows: MetricRow[]
}

export type HealthPayload = {
  status: string
  ok: boolean
  source: string
  last_updated_file: string | null
  display_years: number[]
  daily_in_rows: number
}

export type RowStyle = {
  kind: string
  category_cell?: string
}

export type PptSummaryPayload = {
  columns: string[]
  rows: Record<string, string>[]
  row_styles: RowStyle[]
  meta: {
    target_year: number
    target_month: number
    year_columns: number[]
    months: number[]
    period_label: string
    growth_cols: string[]
    columns: string[]
  } | null
}

export type MonthlyYoyCell = [string, string]

export type MonthlyYoyTablePayload = {
  columns: string[]
  rows: {
    category: string
    label: string
    yoy_cells: MonthlyYoyCell[]
    ytd_yoy: MonthlyYoyCell
  }[]
  row_styles: RowStyle[]
  curr_year: number
  prev_year: number
}

export type InternationalPayload = {
  ok: boolean
  meta: string
  rows: number
  available_years: number[]
  curr_year: number
  curr_month: number
  year_columns: number[]
  monthly_figure: PlotlyFigure | null
  ppt_summary: PptSummaryPayload
  yoy_figure: PlotlyFigure | null
  monthly_yoy_table: MonthlyYoyTablePayload | null
}

export type HolidayCalendarDay = {
  date: string
  weekday: string
  day: number
  month: string
  kind: 'official' | 'weekend' | 'leave' | 'plain'
}

export type HolidayTrackerRow = {
  year: number
  label: string
  al_applicable: boolean
  al_reason: string | null
  days: HolidayCalendarDay[]
}

export type HolidayCpTable = {
  columns: string[]
  rows: Record<string, string | number | null>[]
  yoy_columns: string[]
}

export type HolidayOptions = {
  contexts: string[]
  directions: string[]
  inbound_segments: string[]
  outbound_segments: string[]
  variants: string[]
  holidays_by_region: Record<string, string[]>
  holiday_display: Record<string, string>
  default_direction: Record<string, string>
}

export type HolidayPayload = {
  ok: boolean
  meta: string
  message?: string
  region: string
  context: string
  holiday?: string
  holiday_label?: string
  variant?: string
  direction?: string
  segment?: string
  flow_label?: string
  overview_figure?: PlotlyFigure | null
  daily_figure?: PlotlyFigure | null
  bar_total_figure?: PlotlyFigure | null
  bar_avg_figure?: PlotlyFigure | null
  cp_figure?: PlotlyFigure | null
  cp_table?: HolidayCpTable | null
  tracker: HolidayTrackerRow[]
  hk_meta: Record<string, { al_applicable?: boolean; al_reason?: string | null }>
  al_warnings?: string[]
}

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${path}: ${text}`)
  }
  return res.json() as Promise<T>
}

export function holidayQuery(params: {
  context: string
  holiday: string
  direction: string
  segment: string
  variant: string
}): string {
  const q = new URLSearchParams(params)
  return `/api/holiday?${q.toString()}`
}

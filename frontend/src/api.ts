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

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${path}: ${text}`)
  }
  return res.json() as Promise<T>
}

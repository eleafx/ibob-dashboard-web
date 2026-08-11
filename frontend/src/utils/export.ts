import type { PlotlyFigure } from '../api'

function escapeCsvCell(val: unknown): string {
  const s = val == null ? '' : String(val)
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/** Export a table given headers and 2D row data (arrays of values). */
export function exportTableCsv(
  filename: string,
  headers: string[],
  rows: (string | number | null | undefined)[][],
) {
  const lines = [headers.map(escapeCsvCell).join(',')]
  for (const row of rows) {
    lines.push(row.map(escapeCsvCell).join(','))
  }
  downloadCsv(filename, lines.join('\n'))
}

type CsvExportMeta = {
  headers?: string[]
  rows?: (string | number | null | undefined)[][]
}

function readCsvExportMeta(figure: PlotlyFigure): CsvExportMeta | null {
  const layout = figure.layout as Record<string, unknown> | undefined
  const meta = layout?.meta
  if (!meta || typeof meta !== 'object') return null
  const csv = (meta as Record<string, unknown>).csv_export
  if (!csv || typeof csv !== 'object') return null
  return csv as CsvExportMeta
}

/**
 * Export chart trace data as CSV.
 * Prefers backend-provided layout.meta.csv_export (complete data + abs values).
 * Falls back to aligning traces by x-value; remaps numeric tickvals → ticktext.
 */
export function exportChartCsv(filename: string, figure: PlotlyFigure) {
  const enriched = readCsvExportMeta(figure)
  if (enriched?.headers?.length && enriched.rows) {
    exportTableCsv(filename, enriched.headers, enriched.rows)
    return
  }

  const traces = (figure.data ?? []) as Record<string, unknown>[]
  if (!traces.length) return

  const layout = (figure.layout ?? {}) as Record<string, unknown>
  const xaxis = (layout.xaxis ?? {}) as Record<string, unknown>
  const tickvals = (xaxis.tickvals ?? []) as unknown[]
  const ticktext = (xaxis.ticktext ?? []) as unknown[]
  const tickMap = new Map<string, string>()
  for (let i = 0; i < tickvals.length; i++) {
    tickMap.set(String(tickvals[i]), String(ticktext[i] ?? tickvals[i]))
  }

  // Union of all x values across traces (preserves first-seen order)
  const xOrder: string[] = []
  const xSeen = new Set<string>()
  for (const trace of traces) {
    const xs = (trace.x ?? trace.labels ?? []) as unknown[]
    for (const x of xs) {
      const key = String(x)
      if (!xSeen.has(key)) {
        xSeen.add(key)
        xOrder.push(key)
      }
    }
  }

  const headers = ['Date', ...traces.map((t) => String(t.name ?? 'Series'))]
  const rows: string[][] = []
  for (const xKey of xOrder) {
    const label = tickMap.get(xKey) ?? xKey
    const row: string[] = [escapeCsvCell(label)]
    for (const trace of traces) {
      const xs = (trace.x ?? trace.labels ?? []) as unknown[]
      const ys = (trace.y ?? trace.values ?? []) as unknown[]
      const idx = xs.findIndex((x) => String(x) === xKey)
      const y = idx >= 0 ? ys[idx] : null
      row.push(y != null ? String(y) : '')
    }
    rows.push(row)
  }

  const lines = [headers.map(escapeCsvCell).join(',')]
  for (const row of rows) {
    lines.push(row.join(','))
  }
  downloadCsv(filename, lines.join('\n'))
}

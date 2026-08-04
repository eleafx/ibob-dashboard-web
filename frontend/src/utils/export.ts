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

/**
 * Export chart trace data as CSV.
 * First column = x-axis labels (from the first trace).
 * Each subsequent column = one trace's y-values, keyed by trace name.
 */
export function exportChartCsv(filename: string, figure: PlotlyFigure) {
  const traces = (figure.data ?? []) as Record<string, unknown>[]
  if (!traces.length) return

  const firstTrace = traces[0]
  const xData = (firstTrace.x ?? firstTrace.labels ?? []) as unknown[]

  const headers = ['Date', ...traces.map((t) => String(t.name ?? 'Series'))]

  const rows: string[][] = []
  for (let i = 0; i < xData.length; i++) {
    const row: string[] = [escapeCsvCell(xData[i])]
    for (const trace of traces) {
      const yArr = (trace.y ?? trace.values ?? []) as unknown[]
      row.push(yArr[i] != null ? String(yArr[i]) : '')
    }
    rows.push(row)
  }

  const lines = [headers.map(escapeCsvCell).join(',')]
  for (const row of rows) {
    lines.push(row.join(','))
  }
  downloadCsv(filename, lines.join('\n'))
}

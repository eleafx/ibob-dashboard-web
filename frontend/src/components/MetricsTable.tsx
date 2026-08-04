import type { MetricRow } from '../api'
import { exportTableCsv } from '../utils/export'

type Props = {
  title: string
  headers: string[]
  rows: MetricRow[]
}

export function MetricsTable({ title, headers, rows }: Props) {
  function handleExport() {
    const dataRows = rows.map((r) => [r.label, ...r.values])
    exportTableCsv(`${title.replace(/\s+/g, '_')}.csv`, headers, dataRows)
  }

  return (
    <div className="metrics-table-wrap">
      <div className="table-header-row">
        <h3>{title}</h3>
        <button type="button" className="export-btn" onClick={handleExport} title="Export CSV">
          ⤓ CSV
        </button>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              {headers.map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <td className="row-label">{row.label}</td>
                {row.values.map((v, i) => (
                  <td
                    key={`${row.label}-${i}`}
                    className={
                      v.startsWith('+')
                        ? 'pos'
                        : v.startsWith('-') && v !== '—'
                          ? 'neg'
                          : undefined
                    }
                  >
                    {v}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

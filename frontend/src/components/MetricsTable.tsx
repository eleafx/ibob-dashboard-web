import type { MetricRow } from '../api'

type Props = {
  title: string
  headers: string[]
  rows: MetricRow[]
}

export function MetricsTable({ title, headers, rows }: Props) {
  return (
    <div className="metrics-table-wrap">
      <h3>{title}</h3>
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

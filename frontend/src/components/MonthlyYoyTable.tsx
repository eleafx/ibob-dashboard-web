import type { MonthlyYoyTablePayload, RowStyle } from '../api'
import { exportTableCsv } from '../utils/export'

type Props = {
  data: MonthlyYoyTablePayload
}

function rowClass(style: RowStyle | undefined): string {
  const kind = style?.kind ?? 'default'
  if (kind === 'asean_total') return 'asean-total'
  if (kind === 'g7_total') return 'g7-total'
  if (kind === 'grand_total') return 'grand-total'
  return ''
}

export function MonthlyYoyTable({ data }: Props) {
  const { columns, rows, row_styles, curr_year, prev_year } = data
  const skipCategory = new Set(['middle', 'end'])

  function handleExport() {
    // Rich CSV: YoY % + absolute values per month, YTD, vs 2018, plus provisional months
    const monthLabels = data.month_labels ?? columns.slice(2, -2)
    const headers = ['Category', 'Market']
    for (const m of monthLabels) {
      headers.push(
        `${m} YoY %`,
        `${m} ${curr_year}`,
        `${m} ${prev_year}`,
        `${m} ${curr_year} Absolute`,
        `${m} ${prev_year} Absolute`,
      )
    }
    headers.push(
      'YTD YoY %',
      `YTD ${curr_year}`,
      `YTD ${prev_year}`,
      `YTD ${curr_year} Absolute`,
      `YTD ${prev_year} Absolute`,
      'vs 2018',
      'vs 2018 Absolute (baseline)',
    )

    // Provisional incomplete months (if any)
    const provisionalMonths = new Set<string>()
    for (const row of rows) {
      for (const p of row.provisional ?? []) {
        provisionalMonths.add(p.month)
      }
    }
    const provisionalOrder = [...provisionalMonths]
    for (const m of provisionalOrder) {
      headers.push(
        `${m} YoY % (provisional)`,
        `${m} ${curr_year} (provisional)`,
        `${m} ${prev_year} (provisional)`,
        `${m} ${curr_year} Absolute (provisional)`,
        `${m} ${prev_year} Absolute (provisional)`,
      )
    }

    const dataRows = rows.map((row) => {
      const out: (string | number)[] = [row.category, row.label]
      for (let i = 0; i < monthLabels.length; i++) {
        const abs = row.abs_cells?.[i]
        out.push(
          row.yoy_cells[i]?.[0] ?? '—',
          abs?.curr ?? '',
          abs?.prev ?? '',
          abs?.curr_abs ?? '',
          abs?.prev_abs ?? '',
        )
      }
      out.push(
        row.ytd_yoy[0],
        row.ytd_abs?.curr ?? '',
        row.ytd_abs?.prev ?? '',
        row.ytd_abs?.curr_abs ?? '',
        row.ytd_abs?.prev_abs ?? '',
        row.vs_2018?.[0] ?? '—',
        row.ytd_abs?.base_abs ?? '',
      )
      const byMonth = new Map((row.provisional ?? []).map((p) => [p.month, p]))
      for (const m of provisionalOrder) {
        const p = byMonth.get(m)
        out.push(
          p?.yoy ?? '—',
          p?.curr ?? '',
          p?.prev ?? '',
          p?.curr_abs ?? '',
          p?.prev_abs ?? '',
        )
      }
      return out
    })
    exportTableCsv('Monthly_YoY.csv', headers, dataRows)
  }

  return (
    <div className="ppt-table-wrap">
      <div className="table-header-row">
        <button type="button" className="export-btn" onClick={handleExport} title="Export CSV">
          ⤓ CSV
        </button>
      </div>
      <div className="table-scroll">
        <table className="ppt-table monthly-yoy">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => {
              const style = row_styles[idx]
              const cstate = style?.category_cell ?? 'none'
              const kind = style?.kind ?? 'default'
              let rowspan: number | undefined
              if (cstate === 'start' || cstate === 'single') {
                rowspan = 1
                if (cstate === 'start') {
                  for (let j = idx + 1; j < row_styles.length; j++) {
                    const nxt = row_styles[j]?.category_cell
                    if (nxt === 'middle' || nxt === 'end') {
                      rowspan++
                      if (nxt === 'end') break
                    } else break
                  }
                }
              }

              return (
                <tr key={`${row.label}-${idx}`} className={rowClass(style)}>
                  {!skipCategory.has(cstate) ? (
                    <td className="col-category" rowSpan={rowspan}>
                      {cstate === 'none' ? '' : row.category}
                    </td>
                  ) : null}
                  <td
                    className={
                      kind === 'group_child' ? 'col-market group-child' : 'col-market'
                    }
                  >
                    {row.label}
                  </td>
                  {row.yoy_cells.map(([text, color], i) => (
                    <td key={`${row.label}-m${i}`} style={{ color }}>
                      {text}
                    </td>
                  ))}
                  <td className="col-ytd" style={{ color: row.ytd_yoy[1] }}>
                    {row.ytd_yoy[0]}
                  </td>
                  <td
                    className="col-ytd"
                    style={{ color: row.vs_2018?.[1] ?? '#111' }}
                  >
                    {row.vs_2018?.[0] ?? '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

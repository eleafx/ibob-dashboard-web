import type { PptSummaryPayload, RowStyle } from '../api'

type Props = {
  data: PptSummaryPayload
}

function isGrowthCol(col: string, growthCols: string[]): boolean {
  return growthCols.includes(col) || col.includes(' v ') || col.startsWith('vs ')
}

function cellColor(col: string, val: string, growthCols: string[]): string | undefined {
  if (!isGrowthCol(col, growthCols) || val === '—') return undefined
  if (val.startsWith('+')) return 'var(--pos)'
  if (val.startsWith('-')) return 'var(--neg)'
  return undefined
}

function rowClass(style: RowStyle | undefined): string {
  const kind = style?.kind ?? 'default'
  if (kind === 'asean_total') return 'asean-total'
  if (kind === 'g7_total') return 'g7-total'
  if (kind === 'grand_total') return 'grand-total'
  return ''
}

export function PptSummaryTable({ data }: Props) {
  const { columns, rows, row_styles, meta } = data
  const growthCols = meta?.growth_cols ?? []
  const skipCategory = new Set(['middle', 'end'])

  return (
    <div className="ppt-table-wrap">
      <div className="table-scroll">
        <table className="ppt-table">
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
                <tr key={`${row.Market}-${idx}`} className={rowClass(style)}>
                  {!skipCategory.has(cstate) ? (
                    <td className="col-category" rowSpan={rowspan}>
                      {cstate === 'none' ? '' : row.Category}
                    </td>
                  ) : null}
                  <td
                    className={
                      kind === 'group_child' ? 'col-market group-child' : 'col-market'
                    }
                  >
                    {row.Market}
                  </td>
                  {columns.slice(2).map((col) => {
                    const val = row[col] ?? '—'
                    return (
                      <td
                        key={col}
                        className={col === columns[2] ? 'col-main' : undefined}
                        style={{ color: cellColor(col, val, growthCols) }}
                      >
                        {val}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

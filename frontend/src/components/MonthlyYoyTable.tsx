import type { MonthlyYoyTablePayload, RowStyle } from '../api'

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
  const { columns, rows, row_styles } = data
  const skipCategory = new Set(['middle', 'end'])

  return (
    <div className="ppt-table-wrap">
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
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

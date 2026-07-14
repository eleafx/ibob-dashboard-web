import Plot from 'react-plotly.js'
import type { Data, Layout } from 'plotly.js'
import type { PlotlyFigure } from '../api'

type Props = {
  figure: PlotlyFigure
  className?: string
}

export function PlotlyChart({ figure, className }: Props) {
  const layoutHeight =
    typeof figure.layout?.height === 'number' ? figure.layout.height : 400

  return (
    <div className={className}>
      <Plot
        data={(figure.data ?? []) as Data[]}
        layout={{
          autosize: true,
          ...((figure.layout ?? {}) as Partial<Layout>),
        }}
        useResizeHandler
        style={{ width: '100%', height: layoutHeight }}
        config={{ displayModeBar: false, responsive: true }}
      />
    </div>
  )
}

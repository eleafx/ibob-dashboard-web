import Plot from 'react-plotly.js'
import type { PlotlyFigure } from '../api'

type Props = {
  figure: PlotlyFigure
}

export function PlotlyChart({ figure }: Props) {
  return (
    <Plot
      data={(figure.data ?? []) as Plotly.Data[]}
      layout={{
        autosize: true,
        ...((figure.layout ?? {}) as Partial<Plotly.Layout>),
      }}
      useResizeHandler
      style={{ width: '100%', height: '400px' }}
      config={{ displayModeBar: false, responsive: true }}
    />
  )
}

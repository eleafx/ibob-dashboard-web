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
        config={{
          displayModeBar: true,
          modeBarButtonsToRemove: [
            'lasso2d',
            'select2d',
            'sendDataToCloud',
            'autoScale2d',
            'toggleSpikelines',
          ],
          displaylogo: false,
          responsive: true,
          toImageButtonOptions: {
            format: 'png',
            filename: 'ibob-chart',
            height: 720,
            width: 1280,
          },
        }}
      />
    </div>
  )
}

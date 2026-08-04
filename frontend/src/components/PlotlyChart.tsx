import Plot from 'react-plotly.js'
import type { Data, Layout } from 'plotly.js'
import type { PlotlyFigure } from '../api'
import { exportChartCsv } from '../utils/export'

type Props = {
  figure: PlotlyFigure
  className?: string
}

export function PlotlyChart({ figure, className }: Props) {
  const layoutHeight =
    typeof figure.layout?.height === 'number' ? figure.layout.height : 400

  function handleExport() {
    const title =
      typeof figure.layout?.title === 'string'
        ? figure.layout.title
        : figure.layout?.title && typeof figure.layout.title === 'object'
          ? (figure.layout.title as Record<string, unknown>).text
          : 'chart'
    exportChartCsv(`${String(title ?? 'chart').replace(/\s+/g, '_')}.csv`, figure)
  }

  return (
    <div className={className} style={{ position: 'relative' }}>
      <button type="button" className="export-btn chart-export" onClick={handleExport} title="Export chart data as CSV">
        ⤓ CSV
      </button>
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

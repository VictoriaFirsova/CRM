interface KpiCardProps {
  label: string
  value: string | number
  trend?: { value: string; positive?: boolean }
  sparkline?: number[]
}

function MiniSparkline({ data }: { data: number[] }) {
  const max = Math.max(...data, 1)
  const min = Math.min(...data, 0)
  const range = max - min || 1
  const w = 80
  const h = 28
  const points = data
    .map((v, i) => {
      const x = (i / (data.length - 1 || 1)) * w
      const y = h - ((v - min) / range) * h
      return `${x},${y}`
    })
    .join(' ')

  return (
    <svg width={w} height={h} className="text-foreground-faint opacity-60">
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  )
}

export default function KpiCard({ label, value, trend, sparkline }: KpiCardProps) {
  const defaultSpark = sparkline ?? [3, 5, 4, 7, 6, 8, 7, 9, 8, 10]

  return (
    <div className="kpi-card">
      <div className="flex items-start justify-between gap-2">
        <span className="kpi-label">{label}</span>
        <MiniSparkline data={defaultSpark} />
      </div>
      <div>
        <p className="kpi-value">{value}</p>
        {trend && (
          <p className={trend.positive !== false ? 'kpi-trend-up' : 'kpi-trend-down'}>
            {trend.positive !== false ? '▲' : '▼'} {trend.value}
          </p>
        )}
      </div>
    </div>
  )
}

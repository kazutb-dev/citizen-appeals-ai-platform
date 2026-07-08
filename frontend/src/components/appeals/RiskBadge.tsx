import { useLabels } from '../../i18n/labels'
import type { RiskLevel } from '../../types/common'

const STYLES: Record<RiskLevel, string> = {
  critical: 'bg-risk-critical/15 text-risk-critical border-risk-critical/40',
  high: 'bg-risk-high/15 text-risk-high border-risk-high/40',
  medium: 'bg-risk-medium/15 text-risk-medium border-risk-medium/40',
  low: 'bg-risk-low/15 text-risk-low border-risk-low/40',
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  const labels = useLabels()
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${STYLES[level] ?? STYLES.low}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${level === 'critical' ? 'animate-pulseDot' : ''} bg-current`}
      />
      {labels.risk(level)}
    </span>
  )
}

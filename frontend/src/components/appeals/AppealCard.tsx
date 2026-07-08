import { format } from 'date-fns'
import { Link } from 'react-router-dom'
import type { AppealBrief } from '../../types/appeal'
import { useLabels, useDateFnsLocale } from '../../i18n/labels'
import { RiskBadge } from './RiskBadge'
import { StatusBadge } from './StatusBadge'

export function AppealCard({ appeal }: { appeal: AppealBrief }) {
  const labels = useLabels()
  const dfLocale = useDateFnsLocale()
  return (
    <Link
      to={`/appeals/${appeal.id}`}
      className="card block p-4 transition hover:border-border-light hover:shadow-glow"
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="font-mono text-xs text-navy-400">#{appeal.id}</span>
        <div className="flex gap-2">
          <RiskBadge level={appeal.risk_level} />
          <StatusBadge status={appeal.status} />
        </div>
      </div>
      <p className="line-clamp-2 text-sm font-medium text-navy-100">{appeal.title}</p>
      <div className="mt-3 flex items-center justify-between text-xs text-navy-400">
        <span>
          {labels.category(appeal.category)} · {appeal.region}
        </span>
        <span className="font-mono">
          {format(new Date(appeal.submitted_at), 'dd MMM HH:mm', { locale: dfLocale })}
        </span>
      </div>
    </Link>
  )
}

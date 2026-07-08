import { useLabels } from '../../i18n/labels'
import type { AppealStatus } from '../../types/common'

const STYLES: Record<AppealStatus, string> = {
  new: 'bg-slate-500/15 text-navy-200 border-slate-500/40',
  analyzing: 'bg-accent/15 text-teal-400 border-accent/40',
  pending_review: 'bg-teal-400/10 text-teal-400 border-primary/40',
  in_progress: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/40',
  escalated: 'bg-risk-critical/15 text-risk-critical border-risk-critical/40',
  resolved: 'bg-risk-low/15 text-risk-low border-risk-low/40',
  rejected: 'bg-slate-600/20 text-navy-300 border-slate-600/40',
  duplicate: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
}

export function StatusBadge({ status }: { status: AppealStatus }) {
  const labels = useLabels()
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STYLES[status] ?? STYLES.new}`}
    >
      {labels.status(status)}
    </span>
  )
}

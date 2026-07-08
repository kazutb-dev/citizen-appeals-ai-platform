import { format } from 'date-fns'
import { AlertTriangle, Copy, Network, UserX } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import type { AppealBrief } from '../../types/appeal'
import { useLabels, useDateFnsLocale } from '../../i18n/labels'
import { EmptyState } from '../common/EmptyState'
import { RiskBadge } from './RiskBadge'
import { StatusBadge } from './StatusBadge'

export function AppealTable({ appeals }: { appeals: AppealBrief[] }) {
  const { t } = useTranslation()
  const labels = useLabels()
  const dfLocale = useDateFnsLocale()
  if (!appeals.length) {
    return <EmptyState title={t('appeals.notFound')} hint={t('appeals.notFoundHint')} />
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-navy-400">
            <th className="px-4 py-3">{t('table.number')}</th>
            <th className="px-4 py-3">{t('table.requester')}</th>
            <th className="px-4 py-3">{t('table.subject')}</th>
            <th className="px-4 py-3">{t('table.category')}</th>
            <th className="px-4 py-3">{t('table.location')}</th>
            <th className="px-4 py-3">{t('table.risk')}</th>
            <th className="px-4 py-3">{t('table.status')}</th>
            <th className="px-4 py-3">{t('table.date')}</th>
            <th className="px-4 py-3">{t('table.agents')}</th>
          </tr>
        </thead>
        <tbody>
          {appeals.map((a) => (
            <tr
              key={a.id}
              className="border-b border-border/50 transition-colors hover:bg-surface-card/60"
            >
              <td className="px-4 py-3 font-mono text-navy-400">#{a.id}</td>
              <td className="px-4 py-3 text-navy-200">{a.requester?.full_name ?? '—'}</td>
              <td className="max-w-[280px] px-4 py-3">
                <Link to={`/appeals/${a.id}`} className="line-clamp-2 text-navy-100 hover:text-teal-400">
                  {a.title}
                </Link>
              </td>
              <td className="px-4 py-3 text-navy-300">{labels.category(a.category)}</td>
              <td className="px-4 py-3 text-navy-300">{a.region}</td>
              <td className="px-4 py-3">
                <RiskBadge level={a.risk_level} />
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={a.status} />
              </td>
              <td className="px-4 py-3 font-mono text-xs text-navy-400">
                {format(new Date(a.submitted_at), 'dd.MM.yy HH:mm', { locale: dfLocale })}
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1.5">
                  {a.is_escalated && <AlertTriangle className="h-4 w-4 text-risk-critical" aria-label={t('appeals.escalated')} />}
                  {a.is_campaign && <Network className="h-4 w-4 text-risk-high" aria-label={t('appeals.campaign')} />}
                  {a.is_duplicate && <Copy className="h-4 w-4 text-amber-400" aria-label={t('appeals.duplicate')} />}
                  {a.from_repeat_complainant && <UserX className="h-4 w-4 text-navy-300" aria-label={t('appeals.repeatComplainant')} />}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

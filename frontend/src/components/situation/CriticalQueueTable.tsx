import { format } from 'date-fns'
import { ExternalLink, Loader2, ShieldAlert, UserCheck } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { escalateAppeal, updateAppealStatus } from '../../api/appeals'
import { useDateFnsLocale, useLabels } from '../../i18n/labels'
import type { CriticalQueueItem } from '../../types/situation'
import { EmptyState } from '../common/EmptyState'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface Props {
  items?: CriticalQueueItem[]
  isLoading: boolean
  isError: boolean
}

export function CriticalQueueTable({ items, isLoading, isError }: Props) {
  const { t } = useTranslation()
  const labels = useLabels()
  const locale = useDateFnsLocale()
  const queryClient = useQueryClient()

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['situation-summary'] }),
      queryClient.invalidateQueries({ queryKey: ['situation-critical-queue'] }),
      queryClient.invalidateQueries({ queryKey: ['situation-hotspots'] }),
      queryClient.invalidateQueries({ queryKey: ['situation-ai-actions'] }),
    ])
  }

  const escalateMutation = useMutation({
    mutationFn: (appealId: number) => escalateAppeal(appealId),
    onSuccess: refresh,
  })

  const assignMutation = useMutation({
    mutationFn: (appealId: number) =>
      updateAppealStatus(appealId, 'in_progress', 'Назначено в работу из ситуационного центра'),
    onSuccess: refresh,
  })

  if (isLoading) return <LoadingSpinner label={t('situationOps.loadingQueue')} />
  if (isError) return <EmptyState title={t('situationOps.loadError')} hint={t('situationOps.queueLoadErrorHint')} />
  if (!items?.length) {
    return <EmptyState title={t('situationOps.queueEmptyTitle')} hint={t('situationOps.queueEmptyHint')} />
  }

  return (
    <div className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-navy-100">{t('situationOps.queueTitle')}</h2>
          <p className="mt-1 text-xs text-navy-400">{t('situationOps.queueSubtitle')}</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-navy-400">
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">{t('table.date')}</th>
              <th className="px-4 py-3">{t('table.location')}</th>
              <th className="px-4 py-3">{t('table.category')}</th>
              <th className="px-4 py-3">SLA deadline</th>
              <th className="px-4 py-3">{t('situationOps.responsible')}</th>
              <th className="px-4 py-3">{t('table.status')}</th>
              <th className="px-4 py-3">{t('situationOps.priority')}</th>
              <th className="px-4 py-3">{t('situationOps.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => {
              const overdue = new Date(item.sla_deadline).getTime() < Date.now()
              return (
                <tr key={item.id} className="border-b border-border/50 hover:bg-surface-card/50">
                  <td className="px-4 py-3 font-mono text-navy-300">#{item.id}</td>
                  <td className="px-4 py-3 text-xs text-navy-300">
                    {format(new Date(item.submitted_at), 'dd.MM HH:mm', { locale })}
                  </td>
                  <td className="px-4 py-3 text-navy-200">{item.region}</td>
                  <td className="px-4 py-3 text-navy-200">{item.category_label || labels.category(item.category)}</td>
                  <td className={`px-4 py-3 text-xs font-medium ${overdue ? 'text-risk-critical' : 'text-navy-300'}`}>
                    {format(new Date(item.sla_deadline), 'dd.MM HH:mm', { locale })}
                  </td>
                  <td className="px-4 py-3 text-navy-200">{item.responsible}</td>
                  <td className="px-4 py-3 text-navy-200">{labels.status(item.status)}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-pill px-2 py-1 text-xs font-semibold ${
                        item.priority === 'P0'
                          ? 'bg-risk-critical/15 text-risk-critical'
                          : 'bg-risk-medium/15 text-risk-medium'
                      }`}
                    >
                      {item.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-2">
                      <Link to={`/appeals/${item.id}`} className="btn-ghost !px-3 !py-1.5 text-xs">
                        <ExternalLink className="h-3.5 w-3.5" />
                        {t('situationOps.open')}
                      </Link>
                      <button
                        type="button"
                        disabled={item.is_escalated || escalateMutation.isPending}
                        onClick={() => escalateMutation.mutate(item.id)}
                        className="btn-ghost !px-3 !py-1.5 text-xs disabled:opacity-50"
                      >
                        {escalateMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldAlert className="h-3.5 w-3.5" />}
                        {t('situationOps.escalate')}
                      </button>
                      <button
                        type="button"
                        disabled={item.status === 'in_progress' || assignMutation.isPending}
                        onClick={() => assignMutation.mutate(item.id)}
                        className="btn-ghost !px-3 !py-1.5 text-xs disabled:opacity-50"
                      >
                        {assignMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <UserCheck className="h-3.5 w-3.5" />}
                        {t('situationOps.assign')}
                      </button>
                    </div>
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

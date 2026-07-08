import { Bot, Sparkles } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { AiActionsOut } from '../../types/situation'
import { EmptyState } from '../common/EmptyState'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface Props {
  data?: AiActionsOut
  isLoading: boolean
  isError: boolean
}

export function AiActionPanel({ data, isLoading, isError }: Props) {
  const { t } = useTranslation()

  if (isLoading) return <LoadingSpinner label={t('situationOps.loadingActions')} />
  if (isError) return <EmptyState title={t('situationOps.loadError')} hint={t('situationOps.actionsLoadErrorHint')} />
  if (!data?.items.length) {
    return <EmptyState title={t('situationOps.actionsEmptyTitle')} hint={t('situationOps.actionsEmptyHint')} />
  }

  return (
    <div className="card p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-gold" />
            <h2 className="text-sm font-semibold text-navy-100">{t('situationOps.aiTitle')}</h2>
          </div>
          <p className="mt-1 text-xs text-navy-400">{t('situationOps.aiSubtitle')}</p>
        </div>
        <span className={`rounded-pill px-2.5 py-1 text-[11px] font-medium ${data.ai_available ? 'bg-teal-400/15 text-teal-300' : 'bg-risk-medium/15 text-risk-medium'}`}>
          <Bot className="mr-1 inline h-3 w-3" />
          {data.ai_available ? t('situationOps.aiSource') : t('situationOps.ruleSource')}
        </span>
      </div>
      <div className="space-y-3">
        {data.items.map((item, index) => (
          <div key={`${item.problem}-${index}`} className="rounded-xl border border-border bg-surface-card/50 p-4">
            <div className="mb-3 text-sm font-medium text-navy-100">{item.problem}</div>
            <div className="space-y-2 text-xs leading-relaxed">
              <p><span className="text-navy-500">{t('situationOps.recommendedAction')}:</span> <span className="text-navy-200">{item.action}</span></p>
              <p><span className="text-navy-500">{t('situationOps.assignee')}:</span> <span className="text-navy-100">{item.assignee}</span></p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

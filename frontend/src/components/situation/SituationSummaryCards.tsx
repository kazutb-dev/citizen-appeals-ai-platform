import { Activity, AlertTriangle, Copy, ShieldAlert, Timer } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { SituationSnapshot } from '../../types/situation'
import { EmptyState } from '../common/EmptyState'
import { KpiCard } from '../common/KpiCard'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface Props {
  summary?: SituationSnapshot
  isLoading: boolean
  isError: boolean
}

export function SituationSummaryCards({ summary, isLoading, isError }: Props) {
  const { t } = useTranslation()

  if (isLoading) return <LoadingSpinner label={t('situationOps.loadingSummary')} />
  if (isError || !summary) {
    return <EmptyState title={t('situationOps.loadError')} hint={t('situationOps.loadErrorHint')} />
  }

  return (
    <div className="grid grid-cols-2 gap-4 xl:grid-cols-5">
      <KpiCard
        label={t('situationOps.cards.new24h')}
        value={summary.appeals_24h}
        icon={Activity}
        trendPct={summary.appeals_today_trend_pct}
        sub={t('situationOps.period24h')}
      />
      <KpiCard
        label={t('situationOps.cards.criticalOpen')}
        value={summary.critical_open}
        icon={AlertTriangle}
        tone="critical"
        sub={t('situationOps.openNow')}
      />
      <KpiCard
        label={t('situationOps.cards.slaOverdue')}
        value={summary.sla_violations}
        icon={Timer}
        tone="warning"
        sub={t('situationOps.openNow')}
      />
      <KpiCard
        label={t('situationOps.cards.escalations')}
        value={summary.escalations}
        icon={ShieldAlert}
        tone="warning"
        sub={t('situationOps.openNow')}
      />
      <KpiCard
        label={t('situationOps.cards.duplicates24h')}
        value={summary.duplicates_24h}
        icon={Copy}
        sub={t('situationOps.period24h')}
      />
    </div>
  )
}

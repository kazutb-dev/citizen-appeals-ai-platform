import { useQuery } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { fetchAiActions, fetchCriticalQueue, fetchHotspots, fetchSituation } from '../api/command'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { AiActionPanel } from '../components/situation/AiActionPanel'
import { AppealsMapPanel } from '../components/situation/AppealsMapPanel'
import { CriticalQueueTable } from '../components/situation/CriticalQueueTable'
import { HotspotsPanel } from '../components/situation/HotspotsPanel'
import { SituationSummaryCards } from '../components/situation/SituationSummaryCards'

export function SituationCenter() {
  const { t } = useTranslation()

  const summaryQuery = useQuery({
    queryKey: ['situation-summary'],
    queryFn: () => fetchSituation(),
  })
  const queueQuery = useQuery({
    queryKey: ['situation-critical-queue'],
    queryFn: () => fetchCriticalQueue(),
  })
  const hotspotsQuery = useQuery({
    queryKey: ['situation-hotspots'],
    queryFn: () => fetchHotspots({ period_hours: 72 }),
  })
  const aiActionsQuery = useQuery({
    queryKey: ['situation-ai-actions'],
    queryFn: () => fetchAiActions({ period_hours: 72 }),
  })

  if (summaryQuery.isLoading) return <LoadingSpinner label={t('situationOps.loadingPage')} />
  if (summaryQuery.isError || !summaryQuery.data) {
    return <EmptyState title={t('situationOps.loadError')} hint={t('situationOps.loadErrorHint')} />
  }

  const summary = summaryQuery.data
  const updatedAt = new Date(summary.generated_at).toLocaleString()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">{t('titles.situationCenter')}</h1>
        <p className="mt-1 text-sm text-navy-400">
          {t('situationOps.pageSubtitle')} · {t('situationOps.updatedAt', { value: updatedAt })}
        </p>
      </div>

      <SituationSummaryCards
        summary={summary}
        isLoading={summaryQuery.isLoading}
        isError={summaryQuery.isError}
      />

      <CriticalQueueTable
        items={queueQuery.data}
        isLoading={queueQuery.isLoading}
        isError={queueQuery.isError}
      />

      <AppealsMapPanel regions={summary.region_heatmap.map((item) => item.region)} />

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <HotspotsPanel
          data={hotspotsQuery.data}
          isLoading={hotspotsQuery.isLoading}
          isError={hotspotsQuery.isError}
        />
        <AiActionPanel
          data={aiActionsQuery.data}
          isLoading={aiActionsQuery.isLoading}
          isError={aiActionsQuery.isError}
        />
      </div>
    </div>
  )
}

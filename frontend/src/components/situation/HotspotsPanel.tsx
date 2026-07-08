import { AlertTriangle, Building2, MapPin, Timer } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { HotspotsOut } from '../../types/situation'
import { EmptyState } from '../common/EmptyState'
import { LoadingSpinner } from '../common/LoadingSpinner'

interface Props {
  data?: HotspotsOut
  isLoading: boolean
  isError: boolean
}

export function HotspotsPanel({ data, isLoading, isError }: Props) {
  const { t } = useTranslation()
  const [tab, setTab] = useState<'regions' | 'organizations'>('regions')

  if (isLoading) return <LoadingSpinner label={t('situationOps.loadingHotspots')} />
  if (isError) return <EmptyState title={t('situationOps.loadError')} hint={t('situationOps.hotspotsLoadErrorHint')} />

  const items = tab === 'regions' ? (data?.regions ?? []) : (data?.organizations ?? [])

  return (
    <div className="card p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-navy-100">{t('situationOps.hotspotsTitle')}</h2>
          <p className="mt-1 text-xs text-navy-400">{t('situationOps.hotspotsSubtitle')}</p>
        </div>
        <div className="flex gap-2">
          {([
            ['regions', t('situationOps.regions')],
            ['organizations', t('situationOps.organizations')],
          ] as const).map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => setTab(value)}
              className={`rounded-pill px-3 py-1.5 text-xs transition ${
                tab === value ? 'bg-teal-400/20 text-teal-300' : 'bg-surface text-navy-300 hover:text-navy-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {!items.length ? (
        <EmptyState title={t('situationOps.hotspotsEmptyTitle')} hint={t('situationOps.hotspotsEmptyHint')} />
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.name} className="rounded-xl border border-border bg-surface-card/50 p-4">
              <div className="mb-2 flex items-center gap-2">
                {tab === 'regions' ? <MapPin className="h-4 w-4 text-teal-400" /> : <Building2 className="h-4 w-4 text-teal-400" />}
                <h3 className="text-sm font-medium text-navy-100">{item.name}</h3>
              </div>
              <div className="grid gap-2 sm:grid-cols-4">
                <div className="rounded-lg bg-surface px-3 py-2">
                  <div className="text-[11px] uppercase tracking-wide text-navy-500">{t('situationOps.total')}</div>
                  <div className="font-mono text-lg text-navy-100">{item.total}</div>
                </div>
                <div className="rounded-lg bg-risk-critical/10 px-3 py-2">
                  <div className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-risk-critical"><AlertTriangle className="h-3 w-3" />{t('situationOps.critical')}</div>
                  <div className="font-mono text-lg text-risk-critical">{item.critical}</div>
                </div>
                <div className="rounded-lg bg-risk-medium/10 px-3 py-2">
                  <div className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-risk-medium"><Timer className="h-3 w-3" />{t('situationOps.overdue')}</div>
                  <div className="font-mono text-lg text-risk-medium">{item.overdue}</div>
                </div>
                <div className="rounded-lg bg-surface px-3 py-2">
                  <div className="text-[11px] uppercase tracking-wide text-navy-500">{t('situationOps.openNow')}</div>
                  <div className="font-mono text-lg text-navy-100">{item.open_count}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

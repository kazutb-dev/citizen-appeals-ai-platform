import { useQuery } from '@tanstack/react-query'
import {
  AlertTriangle,
  ClipboardList,
  FileText,
  Gauge,
  Send,
  ShieldAlert,
  TrendingUp,
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import {
  fetchEarlyWarning,
  fetchForecast,
  fetchRiskIndex,
} from '../api/intelligence'
import type { WarningSignal } from '../api/intelligence'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

const LEVEL_HEX: Record<string, string> = {
  low: '#22c55e', moderate: '#14b8a6', elevated: '#f59e0b', high: '#f97316', critical: '#dc2626',
}
const SEV_HEX = LEVEL_HEX

function levelLabel(t: (k: string) => string, level: string) {
  const map: Record<string, string> = {
    low: 'intel.levelLow', moderate: 'intel.levelModerate', elevated: 'intel.levelElevated',
    high: 'intel.levelHigh', critical: 'intel.levelCritical',
  }
  return t(map[level] ?? 'intel.levelModerate')
}
function sevLabel(t: (k: string) => string, sev: string) {
  const map: Record<string, string> = {
    critical: 'intel.sevCritical', high: 'intel.sevHigh', medium: 'intel.sevMedium', low: 'intel.sevLow',
  }
  return t(map[sev] ?? 'intel.sevMedium')
}

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
      <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
           style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  )
}

function resolveAssignee(signal: WarningSignal, t: (k: string) => string): string {
  if (signal.category === 'emergency') return t('intel.assigneeEmergency')
  if (signal.category === 'medicines') return t('intel.assigneePharmacy')
  if (signal.scope) return `${t('intel.assigneeRegionPrefix')}: ${signal.scope}`
  return t('intel.assigneeOps')
}

function SignalCard({ s }: { s: WarningSignal }) {
  const { t } = useTranslation()
  const color = SEV_HEX[s.severity] ?? '#f59e0b'
  const firstAction = s.actions[0] ?? t('intel.noAction')
  return (
    <div className="card overflow-hidden p-4" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 shrink-0" style={{ color }} />
            <h4 className="text-sm font-semibold text-navy-100">{s.title}</h4>
          </div>
          <p className="mt-0.5 text-xs text-navy-400">{s.scope}</p>
        </div>
        <span className="shrink-0 rounded-pill px-2 py-0.5 text-[10px] font-semibold uppercase"
              style={{ background: `${color}22`, color }}>{sevLabel(t, s.severity)}</span>
      </div>
      <p className="mt-2 text-xs text-navy-300">{s.predicted_impact}</p>
      <div className="mt-2 flex items-center gap-2">
        <span className="text-[10px] uppercase text-navy-500">{t('intel.confidence')}</span>
        <div className="flex-1"><ConfidenceBar value={s.confidence} /></div>
        <span className="font-mono text-[10px] text-navy-400">{Math.round(s.confidence * 100)}%</span>
      </div>
      <div className="mt-2 grid gap-2 rounded-lg bg-surface p-3 text-xs text-navy-200 md:grid-cols-2">
        <div>
          <p className="text-[10px] uppercase text-navy-500">{t('intel.recommendedAction')}</p>
          <p className="mt-1">{firstAction}</p>
        </div>
        <div>
          <p className="text-[10px] uppercase text-navy-500">{t('intel.assignTo')}</p>
          <p className="mt-1">{resolveAssignee(s, t)}</p>
        </div>
      </div>
    </div>
  )
}

export function IntelligenceCenter() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const risk = useQuery({ queryKey: ['intel-risk'], queryFn: fetchRiskIndex })
  const forecast7 = useQuery({ queryKey: ['intel-forecast', 7], queryFn: () => fetchForecast(7) })
  const forecast14 = useQuery({ queryKey: ['intel-forecast', 14], queryFn: () => fetchForecast(14) })
  const forecast30 = useQuery({ queryKey: ['intel-forecast', 30], queryFn: () => fetchForecast(30) })
  const warning = useQuery({ queryKey: ['intel-warning'], queryFn: fetchEarlyWarning })

  const [selectedSignal, setSelectedSignal] = useState(0)
  const [memoText, setMemoText] = useState('')

  if (risk.isLoading || forecast7.isLoading || forecast14.isLoading || forecast30.isLoading || warning.isLoading) {
    return <LoadingSpinner label={t('common.loading')} />
  }

  if (!risk.data || !forecast7.data || !forecast14.data || !forecast30.data || !warning.data) {
    return <EmptyState title={t('situationOps.loadError')} hint={t('situationOps.loadErrorHint')} />
  }

  const national = risk.data.national
  const activeSignals = warning.data.signals
  const topGrowth = [...forecast30.data.drivers]
    .filter((item) => item.direction === 'up')
    .sort((a, b) => b.change_pct - a.change_pct)
    .slice(0, 3)
  const topDecline = [...forecast30.data.drivers]
    .filter((item) => item.direction === 'down')
    .sort((a, b) => a.change_pct - b.change_pct)
    .slice(0, 3)

  const factors = national.components.filter((component) => component.contribution > 0).slice(0, 5)

  const selected = activeSignals[selectedSignal] ?? activeSignals[0] ?? null
  const buildMemo = () => {
    if (!selected) return ''
    return [
      t('intel.memoHeader'),
      `${t('intel.memoRisk')}: ${Math.round(national.score)} / 100 (${levelLabel(t, national.level)})`,
      `${t('intel.memoSignal')}: ${selected.title}`,
      `${t('intel.memoReason')}: ${selected.predicted_impact}`,
      `${t('intel.memoAction')}: ${selected.actions[0] ?? t('intel.noAction')}`,
      `${t('intel.memoAssignee')}: ${resolveAssignee(selected, t)}`,
    ].join('\n')
  }

  const quickActionsDisabled = !selected

  const periodCards = [
    { days: 7, payload: forecast7.data },
    { days: 14, payload: forecast14.data },
    { days: 30, payload: forecast30.data },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-navy-50">{t('intel.title')}</h1>
        <p className="mt-1 text-sm text-navy-400">{t('intel.subtitle')}</p>
      </div>

      <div className="card p-5">
        <div className="mb-4 flex items-center gap-2">
          <Gauge className="h-4 w-4 text-teal-400" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.riskSummaryTitle')}</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-border bg-surface/40 p-4">
            <p className="text-xs uppercase tracking-wide text-navy-500">{t('intel.riskIndex')}</p>
            <p className="mt-1 text-3xl font-bold text-navy-50">{Math.round(national.score)}</p>
            <p className="mt-1 text-xs" style={{ color: LEVEL_HEX[national.level] ?? '#14b8a6' }}>
              {levelLabel(t, national.level)}
            </p>
          </div>
          <div className="rounded-xl border border-border bg-surface/40 p-4">
            <p className="text-xs uppercase tracking-wide text-navy-500">{t('intel.riskDynamics')}</p>
            <p className="mt-1 text-2xl font-semibold text-navy-50">
              {national.growth_pct > 0 ? '+' : ''}
              {national.growth_pct}%
            </p>
            <p className="mt-1 text-xs text-navy-400">{t('intel.riskDynamicsHint')}</p>
          </div>
          <div className="rounded-xl border border-border bg-surface/40 p-4">
            <p className="text-xs uppercase tracking-wide text-navy-500">{t('intel.confidence')}</p>
            <p className="mt-1 text-2xl font-semibold text-navy-50">{Math.round(forecast7.data.confidence * 100)}%</p>
            <p className="mt-1 text-xs text-navy-400">{t('intel.sourceHint')}</p>
          </div>
        </div>
      </div>

      <div className="card p-5">
        <div className="mb-4 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-risk-high" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.earlyWarningTitle')}</h2>
        </div>
        {activeSignals.length ? (
          <div className="grid gap-3 md:grid-cols-2">
            {activeSignals.slice(0, 6).map((signal, idx) => (
              <button
                key={`${signal.type}-${idx}`}
                type="button"
                onClick={() => setSelectedSignal(idx)}
                className={`text-left transition ${selectedSignal === idx ? 'ring-1 ring-teal-400/50 rounded-xl' : ''}`}
              >
                <SignalCard s={signal} />
              </button>
            ))}
          </div>
        ) : (
          <EmptyState title={t('intel.noSignals')} hint={t('intel.noSignalsHint')} />
        )}
      </div>

      <div className="card p-5">
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-teal-400" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.loadForecastTitle')}</h2>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          {periodCards.map(({ days, payload }) => (
            <div key={days} className="rounded-xl border border-border bg-surface/40 p-4">
              <p className="text-xs uppercase tracking-wide text-navy-500">{t('intel.periodDays', { days })}</p>
              <p className="mt-1 text-2xl font-semibold text-navy-50">{Math.round(payload.expected_total)}</p>
              <p className="mt-1 text-xs text-navy-400">
                {t('intel.change')}: {payload.expected_change_pct > 0 ? '+' : ''}{payload.expected_change_pct}%
              </p>
              <p className="text-xs text-navy-400">{t('intel.expectedCritical')}: {Math.round(payload.expected_critical)}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border border-border bg-surface/40 p-4">
            <p className="text-xs uppercase tracking-wide text-navy-500">{t('intel.topGrowth')}</p>
            {topGrowth.length ? (
              <div className="mt-2 space-y-2 text-sm text-navy-200">
                {topGrowth.map((item) => (
                  <div key={`${item.scope}-${item.key}`} className="flex items-center justify-between gap-2">
                    <span className="truncate">{item.label}</span>
                    <span className="font-mono text-risk-high">+{item.change_pct}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-navy-400">{t('common.noData')}</p>
            )}
          </div>
          <div className="rounded-xl border border-border bg-surface/40 p-4">
            <p className="text-xs uppercase tracking-wide text-navy-500">{t('intel.topDecline')}</p>
            {topDecline.length ? (
              <div className="mt-2 space-y-2 text-sm text-navy-200">
                {topDecline.map((item) => (
                  <div key={`${item.scope}-${item.key}`} className="flex items-center justify-between gap-2">
                    <span className="truncate">{item.label}</span>
                    <span className="font-mono text-risk-low">{item.change_pct}%</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-navy-400">{t('common.noData')}</p>
            )}
          </div>
        </div>
      </div>

      <div className="card p-5">
        <div className="mb-4 flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-teal-400" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.riskFactorsTitle')}</h2>
        </div>
        {factors.length ? (
          <div className="space-y-3">
            {factors.map((factor) => (
              <div key={factor.key} className="rounded-xl border border-border bg-surface/40 p-4">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-navy-100">{factor.label}</p>
                  <span className="font-mono text-xs text-navy-400">{factor.contribution.toFixed(1)}</span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border">
                  <div className="h-full rounded-full bg-teal-400" style={{ width: `${Math.min(100, factor.value * 100)}%` }} />
                </div>
                <p className="mt-2 text-xs text-navy-400">{t('intel.factorHint')}</p>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title={t('common.noData')} hint={t('intel.riskFactorsEmptyHint')} />
        )}
      </div>

      <div className="card p-5">
        <div className="mb-4 flex items-center gap-2">
          <ClipboardList className="h-4 w-4 text-teal-400" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.actionPanelTitle')}</h2>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <button type="button" className="btn-primary" disabled={quickActionsDisabled} onClick={() => navigate('/drafts')}>
            <ClipboardList className="h-4 w-4" />
            {t('intel.createTask')}
          </button>
          <button type="button" className="btn-ghost" disabled={quickActionsDisabled} onClick={() => navigate('/critical')}>
            <AlertTriangle className="h-4 w-4" />
            {t('intel.escalate')}
          </button>
          <button type="button" className="btn-ghost" disabled={quickActionsDisabled} onClick={() => navigate('/integrations')}>
            <Send className="h-4 w-4" />
            {t('intel.assignAgency')}
          </button>
          <button
            type="button"
            className="btn-ghost"
            disabled={quickActionsDisabled}
            onClick={async () => {
              const payload = buildMemo()
              setMemoText(payload)
              if (payload && typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
                try {
                  await navigator.clipboard.writeText(payload)
                } catch {
                  // no-op: textarea keeps generated memo for manual copy
                }
              }
            }}
          >
            <FileText className="h-4 w-4" />
            {t('intel.makeMemo')}
          </button>
        </div>

        <p className="mt-2 text-xs text-navy-500">{t('intel.actionPanelHint')}</p>

        {memoText && (
          <textarea readOnly value={memoText} rows={7} className="input mt-3 w-full resize-y text-sm" />
        )}
      </div>
    </div>
  )
}

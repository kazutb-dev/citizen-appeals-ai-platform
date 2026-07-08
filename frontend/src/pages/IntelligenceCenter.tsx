import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Activity, AlertTriangle, ArrowDownRight, ArrowUpRight, Bot, Gauge,
  Minus, ShieldAlert, Sparkles, TrendingUp,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import {
  fetchCopilot, fetchEarlyWarning, fetchForecast, fetchRegionalComparison, fetchRiskIndex,
} from '../api/intelligence'
import type { CopilotResult, RegionRank, RiskScore, WarningSignal } from '../api/intelligence'
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

function RadialGauge({ score, level }: { score: number; level: string }) {
  const r = 52
  const circ = 2 * Math.PI * r
  const pct = Math.min(100, Math.max(0, score)) / 100
  const color = LEVEL_HEX[level] ?? '#14b8a6'
  return (
    <svg width={148} height={148} viewBox="0 0 148 148" className="shrink-0">
      <circle cx="74" cy="74" r={r} fill="none" strokeWidth="12" className="stroke-border" />
      <motion.circle
        cx="74" cy="74" r={r} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
        strokeDasharray={circ} initial={{ strokeDashoffset: circ }}
        animate={{ strokeDashoffset: circ * (1 - pct) }} transition={{ duration: 1, ease: 'easeOut' }}
        transform="rotate(-90 74 74)"
      />
      <text x="74" y="72" textAnchor="middle" className="fill-navy-50" fontSize="34" fontWeight="700">
        {Math.round(score)}
      </text>
      <text x="74" y="94" textAnchor="middle" className="fill-navy-400" fontSize="12">/ 100</text>
    </svg>
  )
}

function ConfidenceBar({ value }: { value: number }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
      <div className="h-full rounded-full bg-gradient-to-r from-primary to-accent"
           style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  )
}

function TrendIcon({ dir }: { dir: string }) {
  if (dir === 'up') return <ArrowUpRight className="h-4 w-4 text-risk-high" />
  if (dir === 'down') return <ArrowDownRight className="h-4 w-4 text-risk-low" />
  return <Minus className="h-4 w-4 text-navy-400" />
}

function RiskCard({ risk, big }: { risk: RiskScore; big?: boolean }) {
  const { t } = useTranslation()
  const color = LEVEL_HEX[risk.level] ?? '#14b8a6'
  return (
    <div className="card p-5">
      <div className="flex items-center gap-5">
        {big ? <RadialGauge score={risk.score} level={risk.level} /> : (
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl text-xl font-bold"
               style={{ background: `${color}22`, color }}>
            {Math.round(risk.score)}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h3 className={`font-semibold text-navy-50 ${big ? 'text-lg' : 'text-sm'}`}>{risk.label}</h3>
            <span className="rounded-pill px-2 py-0.5 text-[10px] font-semibold uppercase"
                  style={{ background: `${color}22`, color }}>
              {levelLabel(t, risk.level)}
            </span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-navy-400">
            <span>{risk.total_appeals} {t('intel.appeals')}</span>
            <span className="flex items-center gap-1">
              <TrendingUp className="h-3.5 w-3.5" /> {risk.growth_pct > 0 ? '+' : ''}{risk.growth_pct}% {t('intel.growthWeek')}
            </span>
          </div>
          {big && risk.reasons.length > 0 && (
            <ul className="mt-3 space-y-1 text-xs text-navy-300">
              {risk.reasons.map((r, i) => <li key={i}>• {r}</li>)}
            </ul>
          )}
        </div>
      </div>
      {big && (
        <div className="mt-4 space-y-2 border-t border-border pt-4">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-navy-500">{t('intel.components')}</p>
          {risk.components.filter((c) => c.contribution > 0).slice(0, 5).map((c) => (
            <div key={c.key}>
              <div className="mb-0.5 flex justify-between text-[11px]">
                <span className="text-navy-300">{c.label}</span>
                <span className="font-mono text-navy-400">{c.contribution.toFixed(0)}</span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-border">
                <div className="h-full rounded-full" style={{ width: `${Math.min(100, c.value * 100)}%`, background: color }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SignalCard({ s }: { s: WarningSignal }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const color = SEV_HEX[s.severity] ?? '#f59e0b'
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                className="card overflow-hidden p-4" style={{ borderLeft: `3px solid ${color}` }}>
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
      <button onClick={() => setOpen(!open)} className="mt-2 text-[11px] text-teal-400 hover:underline">
        {t('intel.recommendedActions')} {open ? '▲' : '▼'}
      </button>
      {open && (
        <ul className="mt-2 space-y-1 rounded-lg bg-surface p-3 text-xs text-navy-200">
          {s.actions.map((a, i) => <li key={i}>✓ {a}</li>)}
        </ul>
      )}
    </motion.div>
  )
}

function RankRow({ r, showRes }: { r: RegionRank; showRes?: boolean }) {
  const color = LEVEL_HEX[r.level] ?? '#14b8a6'
  return (
    <div className="flex items-center justify-between gap-2 py-1.5 text-sm">
      <span className="truncate text-navy-200">{r.region}</span>
      <div className="flex items-center gap-3 font-mono text-xs">
        {showRes && <span className="text-navy-400">{r.resolution_rate}%</span>}
        <span className="w-10 text-right" style={{ color }}>{r.score}</span>
      </div>
    </div>
  )
}

export function IntelligenceCenter() {
  const { t } = useTranslation()
  const risk = useQuery({ queryKey: ['intel-risk'], queryFn: fetchRiskIndex })
  const forecast = useQuery({ queryKey: ['intel-forecast'], queryFn: () => fetchForecast(7) })
  const warning = useQuery({ queryKey: ['intel-warning'], queryFn: fetchEarlyWarning })
  const comparison = useQuery({ queryKey: ['intel-comparison'], queryFn: fetchRegionalComparison })

  const [region, setRegion] = useState('')
  const [copilot, setCopilot] = useState<CopilotResult | null>(null)
  const [copilotLoading, setCopilotLoading] = useState(false)

  const chartData = useMemo(() => (forecast.data?.series ?? []).map((p) => ({
    day: p.day,
    value: p.predicted,
    histValue: p.is_forecast ? null : p.predicted,
    foreValue: p.is_forecast ? p.predicted : null,
    bandHigh: p.is_forecast ? p.upper : null,
    bandLow: p.is_forecast ? p.lower : null,
  })), [forecast.data])

  const runCopilot = async () => {
    setCopilotLoading(true)
    setCopilot(null)
    try {
      setCopilot(await fetchCopilot(region || undefined))
    } finally {
      setCopilotLoading(false)
    }
  }

  if (risk.isLoading || !risk.data) return <LoadingSpinner label={t('common.loading')} />

  const shortDate = (d: string) => `${d.slice(8, 10)}.${d.slice(5, 7)}`

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-bold text-navy-50">
          <Sparkles className="h-5 w-5 text-teal-400" /> {t('intel.title')}
        </h1>
        <p className="mt-1 text-sm text-navy-400">{t('intel.subtitle')}</p>
      </div>

      {/* Risk index */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-1"><RiskCard risk={risk.data.national} big /></div>
        <div className="lg:col-span-2">
          <div className="card h-full p-5">
            <p className="mb-3 text-sm font-semibold text-navy-100">{t('intel.topRegions')}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {risk.data.regions.slice(0, 6).map((r) => <RiskCard key={r.key} risk={r} />)}
            </div>
          </div>
        </div>
      </div>

      {/* Forecast */}
      <div className="card p-5">
        <div className="mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-teal-400" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.forecast')}</h2>
          <span className="ml-auto text-xs text-navy-500">{t('intel.forecastSubtitle')}</span>
        </div>
        {forecast.data && (
          <>
            <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                { label: t('intel.expectedWeek'), value: Math.round(forecast.data.expected_total), icon: Activity },
                { label: t('intel.vsLastWeek'), value: `${forecast.data.expected_change_pct > 0 ? '+' : ''}${forecast.data.expected_change_pct}%`, icon: TrendingUp },
                { label: t('intel.expectedCritical'), value: Math.round(forecast.data.expected_critical), icon: AlertTriangle },
                { label: t('intel.confidence'), value: `${Math.round(forecast.data.confidence * 100)}%`, icon: Gauge },
              ].map((kpi) => (
                <div key={kpi.label} className="rounded-xl border border-border bg-surface/50 p-3">
                  <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-navy-500">
                    <kpi.icon className="h-3.5 w-3.5" /> {kpi.label}
                  </div>
                  <p className="mt-1 text-2xl font-bold text-navy-50">{kpi.value}</p>
                </div>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <ComposedChart data={chartData} margin={{ top: 6, right: 8, left: -12, bottom: 0 }}>
                <defs>
                  <linearGradient id="fcArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00B0AD" stopOpacity={0.22} />
                    <stop offset="100%" stopColor="#00B0AD" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" tickFormatter={shortDate} tick={{ fill: '#7a8aa0', fontSize: 11 }}
                       interval="preserveStartEnd" minTickGap={28} />
                <YAxis tick={{ fill: '#7a8aa0', fontSize: 11 }} width={38} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#0d1627', border: '1px solid #2c4565', borderRadius: 8, fontSize: 12 }}
                         labelStyle={{ color: '#c9d6e5' }} labelFormatter={(d) => shortDate(String(d))} />
                <Area type="monotone" dataKey="value" stroke="none" fill="url(#fcArea)" isAnimationActive={false} />
                <Line type="monotone" dataKey="histValue" name={t('intel.history')} stroke="#00B0AD" strokeWidth={2} dot={false} connectNulls />
                <Line type="monotone" dataKey="foreValue" name={t('intel.predicted')} stroke="#00B0AD" strokeWidth={2} strokeDasharray="5 4" dot={false} connectNulls />
                <Line type="monotone" dataKey="bandHigh" stroke="#00B0AD" strokeOpacity={0.3} strokeWidth={1} dot={false} connectNulls legendType="none" />
                <Line type="monotone" dataKey="bandLow" stroke="#00B0AD" strokeOpacity={0.3} strokeWidth={1} dot={false} connectNulls legendType="none" />
              </ComposedChart>
            </ResponsiveContainer>
            <div className="mt-4">
              <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-navy-500">{t('intel.drivers')}</p>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {forecast.data.drivers.map((d) => (
                  <div key={`${d.scope}-${d.key}`} className="flex items-center justify-between rounded-lg border border-border bg-surface/40 px-3 py-2">
                    <div className="min-w-0">
                      <p className="truncate text-xs font-medium text-navy-200">{d.label}</p>
                      <p className="text-[10px] uppercase text-navy-500">{d.expected_next} · {Math.round(d.confidence * 100)}%</p>
                    </div>
                    <span className="flex shrink-0 items-center gap-1 font-mono text-xs font-semibold"
                          style={{ color: d.direction === 'up' ? '#f97316' : d.direction === 'down' ? '#22c55e' : '#7a8aa0' }}>
                      <TrendIcon dir={d.direction} />{d.change_pct > 0 ? '+' : ''}{d.change_pct}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Early warning */}
      <div className="card p-5">
        <div className="mb-3 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-risk-high" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.earlyWarning')}</h2>
          <span className="ml-auto text-xs text-navy-500">{t('intel.earlyWarningSubtitle')}</span>
        </div>
        {warning.isLoading ? <LoadingSpinner /> : warning.data && warning.data.total > 0 ? (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {warning.data.signals.map((s, i) => <SignalCard key={i} s={s} />)}
          </div>
        ) : (
          <p className="py-6 text-center text-sm text-navy-400">{t('intel.noSignals')}</p>
        )}
      </div>

      {/* Regional comparison */}
      {comparison.data && (
        <div className="card p-5">
          <div className="mb-4 flex items-center gap-2">
            <Gauge className="h-4 w-4 text-teal-400" />
            <h2 className="text-sm font-semibold text-navy-100">{t('intel.comparison')}</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {([
              ['intel.best', comparison.data.best, '#22c55e', true],
              ['intel.worst', comparison.data.worst, '#dc2626', true],
              ['intel.improving', comparison.data.improving, '#14b8a6', false],
              ['intel.deteriorating', comparison.data.deteriorating, '#f97316', false],
            ] as const).map(([key, list, color, showRes]) => (
              <div key={key} className="rounded-xl border border-border bg-surface/40 p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider" style={{ color }}>{t(key)}</p>
                <div className="divide-y divide-border/60">
                  {list.map((r) => <RankRow key={r.region} r={r} showRes={showRes} />)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Executive Copilot */}
      <div className="card p-5">
        <div className="mb-3 flex items-center gap-2">
          <Bot className="h-4 w-4 text-teal-400" />
          <h2 className="text-sm font-semibold text-navy-100">{t('intel.copilot')}</h2>
          <span className="ml-auto text-xs text-navy-500">{t('intel.copilotSubtitle')}</span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select value={region} onChange={(e) => setRegion(e.target.value)} className="input">
            <option value="">{t('intel.wholeCountry')}</option>
            {risk.data.regions.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}
          </select>
          <button onClick={runCopilot} disabled={copilotLoading} className="btn-primary">
            <Sparkles className="h-4 w-4" />
            {copilotLoading ? t('intel.generating') : t('intel.generateBriefing')}
          </button>
        </div>
        <p className="mt-2 text-[11px] text-navy-500">{t('intel.copilotHint')}</p>
        {copilotLoading && <div className="mt-4"><LoadingSpinner label={t('intel.generating')} /></div>}
        {copilot?.briefing && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                      className="mt-4 whitespace-pre-wrap rounded-xl border border-accent/20 bg-accent/5 p-4 text-sm leading-relaxed text-navy-100">
            {copilot.briefing}
          </motion.div>
        )}
      </div>
    </div>
  )
}

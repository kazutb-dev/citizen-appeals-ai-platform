import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, ClipboardList, ShieldAlert, Timer } from 'lucide-react'
import { fetchSituation } from '../api/command'
import { KpiCard } from '../components/common/KpiCard'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

export function ChiefDoctorDashboard() {
  const { data: s } = useQuery({ queryKey: ['situation'], queryFn: () => fetchSituation() })
  if (!s) return <LoadingSpinner label="Загрузка панели главного врача…" />

  const catMax = Math.max(1, ...s.category_breakdown.map((c) => c.count))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">Панель главного врача</h1>
        <p className="text-xs text-navy-400">Нагрузка по направлениям, инциденты, SLA и эскалации</p>
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <KpiCard label="Обращений сегодня" value={s.appeals_today} icon={ClipboardList} trendPct={s.appeals_today_trend_pct} />
        <KpiCard label="Критических" value={s.critical_open} icon={AlertTriangle} tone="critical" />
        <KpiCard label="Нарушений SLA" value={s.sla_violations} icon={Timer} tone="warning" />
        <KpiCard label="Эскалаций" value={s.escalations} icon={ShieldAlert} tone="warning" />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-navy-100">Нагрузка по направлениям</h2>
          <div className="space-y-3">
            {s.category_breakdown.map((c) => {
              const pct = Math.round((c.count / catMax) * 100)
              return (
                <div key={c.category} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-navy-200">{c.label}</span>
                    <span className="font-mono text-navy-300">{c.count}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-surface">
                    <div className="h-full rounded-full bg-teal-400/70" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-navy-100">Рейтинг больниц</h2>
          <div className="space-y-2">
            {s.hospital_ranking.length ? (
              s.hospital_ranking.map((h) => (
                <div
                  key={h.hospital_id}
                  className="flex items-center justify-between border-b border-border/50 pb-1.5 text-xs last:border-0 last:pb-0"
                >
                  <span className="truncate pr-2 text-navy-200">{h.name}</span>
                  <span className="shrink-0 font-mono text-navy-300">
                    {h.total} · <span className="text-risk-critical">{h.critical}</span>
                  </span>
                </div>
              ))
            ) : (
              <p className="text-xs text-navy-400">Больницы не привязаны (enterprise seed).</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

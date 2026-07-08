import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Building2, MapPin, Pill, Sparkles, TrendingUp } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { fetchExecutiveBrief, fetchSituation } from '../api/command'
import { EmptyState } from '../components/common/EmptyState'
import { KpiCard } from '../components/common/KpiCard'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: ReactNode }) {
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="h-4 w-4 text-teal-400" />
        <h2 className="text-sm font-semibold text-navy-100">{title}</h2>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  )
}

function Row({ left, right }: { left: string; right: string | number }) {
  return (
    <div className="flex items-center justify-between border-b border-border/50 pb-1.5 text-xs last:border-0 last:pb-0">
      <span className="truncate pr-2 text-navy-200">{left}</span>
      <span className="shrink-0 font-mono text-navy-300">{right}</span>
    </div>
  )
}

export function ExecutiveDashboard() {
  const { data: brief } = useQuery({ queryKey: ['exec-brief'], queryFn: () => fetchExecutiveBrief() })
  const { data: s } = useQuery({ queryKey: ['situation'], queryFn: () => fetchSituation() })

  if (!brief || !s) return <LoadingSpinner label="Загрузка исполнительной панели…" />

  const topRegions = [...s.region_heatmap].sort((a, b) => b.critical - a.critical).slice(0, 6)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">Панель руководителя здравоохранения</h1>
        <p className="text-xs text-navy-400">
          Ключевые проблемы, регионы и AI-сводка · {new Date(brief.generated_at).toLocaleString('ru-RU')}
        </p>
      </div>

      <div className="card border-gold/30 p-5">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-gold" />
          <h2 className="text-sm font-semibold text-navy-100">AI Executive Summary</h2>
        </div>
        {brief.ai_available && brief.summary ? (
          <p className="text-base leading-relaxed text-navy-100">{brief.summary}</p>
        ) : (
          <EmptyState title="Локальная модель недоступна" hint="Запустите Ollama для автоматической сводки." />
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <KpiCard label="Обращений сегодня" value={s.appeals_today} icon={TrendingUp} trendPct={s.appeals_today_trend_pct} />
        <KpiCard label="Критических" value={s.critical_open} icon={AlertTriangle} tone="critical" />
        <KpiCard label="Нарушений SLA" value={s.sla_violations} icon={AlertTriangle} tone="warning" />
        <KpiCard label="Лекарства" value={s.medicine_shortage} icon={Pill} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Panel title="Топ проблем" icon={AlertTriangle}>
          {s.category_breakdown.slice(0, 6).map((c) => (
            <Row key={c.category} left={c.label} right={c.count} />
          ))}
        </Panel>
        <Panel title="Топ регионов (критичные)" icon={MapPin}>
          {topRegions.map((r) => (
            <Row key={r.region} left={r.region} right={`${r.critical} / ${r.total}`} />
          ))}
        </Panel>
        <Panel title="Топ больниц" icon={Building2}>
          {s.hospital_ranking.length ? (
            s.hospital_ranking.slice(0, 6).map((h) => (
              <Row key={h.hospital_id} left={h.name} right={h.total} />
            ))
          ) : (
            <p className="text-xs text-navy-400">Больницы не привязаны (enterprise seed).</p>
          )}
        </Panel>
      </div>
    </div>
  )
}

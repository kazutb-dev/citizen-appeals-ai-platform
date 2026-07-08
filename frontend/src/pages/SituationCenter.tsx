import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  Ambulance,
  Bot,
  Brain,
  Building2,
  Layers,
  MapPin,
  Pill,
  ShieldAlert,
  Sparkles,
  Timer,
} from 'lucide-react'
import { useState } from 'react'
import { fetchExecutiveBrief, fetchRootCause, fetchSituation } from '../api/command'
import type { CategoryCount } from '../api/command'
import { EmptyState } from '../components/common/EmptyState'
import { KpiCard } from '../components/common/KpiCard'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useAuth } from '../hooks/useAuth'

function BarRow({
  label,
  value,
  max,
  critical,
}: {
  label: string
  value: number
  max: number
  critical?: number
}) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="truncate pr-2 text-navy-200">{label}</span>
        <span className="shrink-0 font-mono text-navy-300">
          {value}
          {critical ? <span className="text-risk-critical"> · {critical} крит.</span> : null}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface">
        <div className="h-full rounded-full bg-teal-400/70" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export function SituationCenter() {
  const { user } = useAuth()
  const canBrief = ['analyst', 'admin'].includes(user?.role ?? '')
  const [rcCategory, setRcCategory] = useState<string>('')

  const { data: s, isError: sError } = useQuery({ queryKey: ['situation'], queryFn: () => fetchSituation() })
  const { data: brief, isError: briefError } = useQuery({
    queryKey: ['exec-brief'],
    queryFn: () => fetchExecutiveBrief(),
    enabled: canBrief,
  })
  const { data: rootCause, isFetching: rcLoading } = useQuery({
    queryKey: ['root-cause', rcCategory],
    queryFn: () => fetchRootCause(rcCategory),
    enabled: canBrief && !!rcCategory,
  })

  if (sError) return <EmptyState title="Ошибка загрузки" hint="Не удалось получить данные ситуационного центра. Проверьте соединение с бэкендом." />
  if (!s) return <LoadingSpinner label="Загрузка ситуационного центра…" />

  const regionMax = Math.max(1, ...s.region_heatmap.map((r) => r.total))
  const hospitalMax = Math.max(1, ...s.hospital_ranking.map((h) => h.total))
  const catMax = Math.max(1, ...s.category_breakdown.map((c) => c.count))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">Медицинский ситуационный центр</h1>
        <p className="text-xs text-navy-400">
          Единая картина обращений в реальном времени · обновлено{' '}
          {new Date(s.generated_at).toLocaleString('ru-RU')}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard label="Обращений сегодня" value={s.appeals_today} icon={Activity} trendPct={s.appeals_today_trend_pct} />
        <KpiCard label="Критических" value={s.critical_open} icon={AlertTriangle} tone="critical" sub="открытых" />
        <KpiCard label="Нарушений SLA" value={s.sla_violations} icon={Timer} tone="warning" />
        <KpiCard label="Эскалаций" value={s.escalations} icon={ShieldAlert} tone="warning" />
        <KpiCard label="Лекарства" value={s.medicine_shortage} icon={Pill} sub="обращений" />
        <KpiCard label="Скорая/экстренная" value={s.emergency_incidents} icon={Ambulance} tone="critical" />
        <KpiCard label="Кампании / дубли" value={`${s.campaigns} / ${s.duplicates}`} icon={Layers} />
        <KpiCard label="AI-анализов" value={s.ai_runs_today} icon={Bot} tone="success" sub="за сегодня" />
      </div>

      {canBrief && (
        <div className="card p-5">
          <div className="mb-3 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-gold" />
            <h2 className="text-sm font-semibold text-navy-100">AI Executive Brief</h2>
          </div>
          {brief ? (
            brief.ai_available && brief.summary ? (
              <p className="text-sm leading-relaxed text-navy-200">{brief.summary}</p>
            ) : (
              <EmptyState
                title="Локальная модель недоступна"
                hint="Запустите Ollama, чтобы получить AI-сводку. Агрегаты выше рассчитаны по данным."
              />
            )
          ) : briefError ? (
            <EmptyState title="Ошибка загрузки сводки" hint="Проверьте соединение с бэкендом." />
          ) : (
            <LoadingSpinner label="Генерация сводки…" />
          )}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <div className="mb-4 flex items-center gap-2">
            <MapPin className="h-4 w-4 text-teal-400" />
            <h2 className="text-sm font-semibold text-navy-100">Тепловая карта регионов</h2>
          </div>
          <div className="space-y-3">
            {s.region_heatmap.length ? (
              s.region_heatmap.slice(0, 10).map((r) => (
                <BarRow key={r.region} label={r.region} value={r.total} max={regionMax} critical={r.critical} />
              ))
            ) : (
              <EmptyState title="Нет данных по регионам" />
            )}
          </div>
        </div>

        <div className="card p-5">
          <div className="mb-4 flex items-center gap-2">
            <Building2 className="h-4 w-4 text-teal-400" />
            <h2 className="text-sm font-semibold text-navy-100">Рейтинг больниц</h2>
          </div>
          <div className="space-y-3">
            {s.hospital_ranking.length ? (
              s.hospital_ranking.map((h) => (
                <BarRow key={h.hospital_id} label={h.name} value={h.total} max={hospitalMax} critical={h.critical} />
              ))
            ) : (
              <EmptyState title="Больницы не привязаны" hint="Запустите enterprise seed для наполнения." />
            )}
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-navy-100">Обращения по категориям</h2>
          <div className="space-y-3">
            {s.category_breakdown.map((c) => (
              <BarRow key={c.category} label={c.label} value={c.count} max={catMax} />
            ))}
          </div>
        </div>

        <div className="card p-5">
          <div className="mb-4 flex items-center gap-2">
            <Brain className="h-4 w-4 text-gold" />
            <h2 className="text-sm font-semibold text-navy-100">AI-анализ первопричин</h2>
          </div>
          {canBrief ? (
            <>
              <div className="mb-4 flex flex-wrap gap-2">
                {s.category_breakdown.slice(0, 6).map((c: CategoryCount) => (
                  <button
                    key={c.category}
                    onClick={() => setRcCategory(c.category)}
                    className={`rounded-pill px-3 py-1 text-xs transition ${
                      rcCategory === c.category
                        ? 'bg-teal-400/20 text-teal-300'
                        : 'bg-surface text-navy-300 hover:text-navy-100'
                    }`}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
              {!rcCategory ? (
                <p className="text-xs text-navy-400">
                  Выберите категорию для определения корневых причин.
                </p>
              ) : rcLoading ? (
                <LoadingSpinner label="Анализ первопричин…" />
              ) : rootCause && rootCause.ai_available ? (
                <div className="space-y-3">
                  {rootCause.summary && <p className="text-sm text-navy-200">{rootCause.summary}</p>}
                  {rootCause.root_causes.map((rc, i) => (
                    <div key={i} className="rounded-lg border border-border bg-surface p-3">
                      <div className="mb-1 flex items-center justify-between">
                        <span className="text-sm font-medium text-navy-100">{rc.cause}</span>
                        <span className="font-mono text-xs text-gold">
                          {Math.round(rc.likelihood * 100)}%
                        </span>
                      </div>
                      {rc.evidence && <p className="text-xs text-navy-400">{rc.evidence}</p>}
                    </div>
                  ))}
                  {rootCause.recommended_actions.length > 0 && (
                    <ul className="list-inside list-disc space-y-1 text-xs text-navy-300">
                      {rootCause.recommended_actions.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <EmptyState
                  title="Локальная модель недоступна"
                  hint="Запустите Ollama для AI-анализа первопричин."
                />
              )}
            </>
          ) : (
            <EmptyState
              title="Недоступно для вашей роли"
              hint="Анализ первопричин доступен аналитикам и администраторам."
            />
          )}
        </div>
      </div>
    </div>
  )
}

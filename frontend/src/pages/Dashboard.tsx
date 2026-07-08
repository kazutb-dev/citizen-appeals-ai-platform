import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Bot, Clock, FileText, Network } from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  fetchCategories,
  fetchOverview,
  fetchTrends,
} from '../api/analytics'
import { fetchAppeals } from '../api/appeals'
import { fetchClusters } from '../api/clusters'
import { AppealCard } from '../components/appeals/AppealCard'
import { CategoryPie } from '../components/charts/CategoryPie'
import { TrendChart } from '../components/charts/TrendChart'
import { EmptyState } from '../components/common/EmptyState'
import { KpiCard } from '../components/common/KpiCard'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { CLUSTER_STATUS_LABELS } from '../types/cluster'

export function Dashboard() {
  const { data: kpi, isError: kpiError } = useQuery({ queryKey: ['overview'], queryFn: fetchOverview })
  const { data: trends } = useQuery({ queryKey: ['trends'], queryFn: () => fetchTrends(30) })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: fetchCategories })
  const { data: critical } = useQuery({
    queryKey: ['appeals', { risk_level: 'critical', page_size: 5 }],
    queryFn: () => fetchAppeals({ risk_level: 'critical', page_size: 5 }),
  })
  const { data: clusters } = useQuery({ queryKey: ['clusters'], queryFn: () => fetchClusters() })

  if (kpiError) return <EmptyState title="Ошибка загрузки" hint="Не удалось получить данные панели. Проверьте соединение с бэкендом." />
  if (!kpi) return <LoadingSpinner label="Загрузка панели…" />

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 xl:grid-cols-5">
        <KpiCard label="Всего сегодня" value={kpi.appeals_today} icon={FileText} trendPct={kpi.appeals_today_trend_pct} delay={0} />
        <KpiCard label="Критических" value={kpi.critical_open} icon={AlertTriangle} tone="critical" sub="требуют реакции" delay={0.05} />
        <KpiCard label="Групп обращений" value={kpi.campaigns_detected} icon={Network} tone="warning" delay={0.1} />
        <KpiCard label="Обработано ИИ" value={`${kpi.ai_processed_pct}%`} icon={Bot} sub={`${kpi.ai_processed} из ${kpi.total_appeals}`} tone="success" delay={0.15} />
        <KpiCard label="Среднее время ответа" value={`${kpi.avg_response_days} дн`} icon={Clock} delay={0.2} />
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="card p-5 xl:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-navy-200">
            Динамика обращений — 30 дней
          </h2>
          {trends ? <TrendChart data={trends} /> : <LoadingSpinner />}
        </div>
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-navy-200">По категориям</h2>
          {categories ? <CategoryPie data={categories} /> : <LoadingSpinner />}
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-navy-200">Критические обращения</h2>
            <Link to="/critical" className="text-xs text-teal-400 hover:text-teal-300 hover:underline">
              Все →
            </Link>
          </div>
          <div className="space-y-3">
            {critical?.items.length ? (
              critical.items.map((a) => <AppealCard key={a.id} appeal={a} />)
            ) : (
              <EmptyState title="Критических обращений нет" />
            )}
          </div>
        </div>

        <div className="card p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-navy-200">Активные группы</h2>
            <Link to="/clusters" className="text-xs text-teal-400 hover:text-teal-300 hover:underline">
              Все →
            </Link>
          </div>
          <div className="space-y-3">
            {clusters?.length ? (
              clusters.slice(0, 3).map((c) => (
                <Link
                  key={c.id}
                  to={`/clusters/${c.id}`}
                  className="block rounded-lg border border-border bg-surface p-4 transition hover:border-border-light"
                >
                  <div className="mb-1 flex items-center justify-between">
                    <span
                      className={`text-xs font-semibold ${
                        c.status === 'confirmed_campaign' ? 'text-risk-critical' : 'text-teal-400'
                      }`}
                    >
                      {CLUSTER_STATUS_LABELS[c.status]}
                    </span>
                    <span className="font-mono text-xs text-navy-400">
                      {c.appeal_count} обращ.
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-navy-100">{c.name}</p>
                  <p className="mt-1 text-xs text-navy-400">
                    Координация: {Math.round(c.coordination_score * 100)}% · локаций:{' '}
                    {Object.keys(c.region_spread).length}
                  </p>
                </Link>
              ))
            ) : (
              <EmptyState title="Активных групп нет" />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

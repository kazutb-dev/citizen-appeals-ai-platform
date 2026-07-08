import { useQuery } from '@tanstack/react-query'
import { Bot } from 'lucide-react'
import {
  fetchAgentStats,
  fetchCategories,
  fetchRegions,
  fetchTrends,
} from '../api/analytics'
import { CategoryPie } from '../components/charts/CategoryPie'
import { RegionalBar } from '../components/charts/RegionalBar'
import { TrendChart } from '../components/charts/TrendChart'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { AGENT_BY_KEY } from '../components/agents/agentMeta'

export function AnalyticsPage() {
  const { data: trends } = useQuery({ queryKey: ['trends'], queryFn: () => fetchTrends(30) })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: fetchCategories })
  const { data: regions } = useQuery({ queryKey: ['regions'], queryFn: fetchRegions })
  const { data: agents } = useQuery({ queryKey: ['agent-stats'], queryFn: fetchAgentStats })

  return (
    <div className="space-y-6">
      <div className="card p-5">
        <h2 className="mb-4 text-sm font-semibold text-navy-100">Производительность агентов</h2>
        {agents ? (
          <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
            {agents.map((a) => {
              const meta = AGENT_BY_KEY[a.agent]
              const Icon = meta?.icon ?? Bot
              return (
                <div key={a.agent} className="rounded-lg border border-border bg-surface p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${meta?.color ?? 'text-teal-400'}`} />
                    <span className="text-xs font-medium text-navy-200">{a.name}</span>
                  </div>
                  <p className="font-mono text-2xl font-semibold text-navy-50">{a.processed}</p>
                  <p className="text-[11px] text-navy-400">запусков · выявлено: {a.flagged}</p>
                </div>
              )
            })}
          </div>
        ) : (
          <LoadingSpinner />
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="card p-5 xl:col-span-2">
          <h2 className="mb-4 text-sm font-semibold text-navy-100">Динамика за 30 дней</h2>
          {trends ? <TrendChart data={trends} /> : <LoadingSpinner />}
        </div>
        <div className="card p-5">
          <h2 className="mb-4 text-sm font-semibold text-navy-100">Структура по категориям</h2>
          {categories ? <CategoryPie data={categories} /> : <LoadingSpinner />}
        </div>
      </div>

      <div className="card p-5">
        <h2 className="mb-4 text-sm font-semibold text-navy-100">Разрез по регионам</h2>
        {regions ? (
          <RegionalBar data={regions} height={Math.max(360, regions.length * 34)} />
        ) : (
          <LoadingSpinner />
        )}
      </div>
    </div>
  )
}

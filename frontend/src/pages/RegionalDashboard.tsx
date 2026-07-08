import { useQuery } from '@tanstack/react-query'
import { MapPin } from 'lucide-react'
import { fetchSituation } from '../api/command'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

function heatColor(ratio: number): string {
  if (ratio >= 0.15) return 'bg-risk-critical/25 border-risk-critical/50'
  if (ratio >= 0.08) return 'bg-risk-high/20 border-risk-high/50'
  if (ratio > 0) return 'bg-risk-medium/15 border-risk-medium/40'
  return 'bg-surface border-border'
}

export function RegionalDashboard() {
  const { data: s } = useQuery({ queryKey: ['situation'], queryFn: () => fetchSituation() })
  if (!s) return <LoadingSpinner label="Загрузка региональной панели…" />

  const regions = [...s.region_heatmap].sort((a, b) => b.total - a.total)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">Региональная панель</h1>
        <p className="text-xs text-navy-400">
          Обращения и критические сигналы по регионам Республики Казахстан
        </p>
      </div>

      {regions.length ? (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
            {regions.map((r) => {
              const ratio = r.total ? r.critical / r.total : 0
              return (
                <div key={r.region} className={`rounded-xl border p-4 ${heatColor(ratio)}`}>
                  <div className="mb-2 flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-teal-400" />
                    <span className="truncate text-xs font-semibold text-navy-100">{r.region}</span>
                  </div>
                  <p className="font-mono text-2xl font-semibold text-navy-50">{r.total}</p>
                  <p className="text-[11px] text-risk-critical">{r.critical} критических</p>
                </div>
              )
            })}
          </div>

          <div className="card p-5">
            <h2 className="mb-3 text-sm font-semibold text-navy-100">Рейтинг регионов</h2>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-navy-500">
                  <th className="pb-2">Регион</th>
                  <th className="pb-2 text-right">Всего</th>
                  <th className="pb-2 text-right">Критических</th>
                  <th className="pb-2 text-right">Доля крит.</th>
                </tr>
              </thead>
              <tbody>
                {regions.map((r) => (
                  <tr key={r.region} className="border-t border-border/50">
                    <td className="py-2 text-navy-200">{r.region}</td>
                    <td className="py-2 text-right font-mono text-navy-300">{r.total}</td>
                    <td className="py-2 text-right font-mono text-risk-critical">{r.critical}</td>
                    <td className="py-2 text-right font-mono text-navy-400">
                      {r.total ? Math.round((r.critical / r.total) * 100) : 0}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <EmptyState title="Нет данных по регионам" />
      )}
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { ArrowLeft, UserX } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { fetchRequester, fetchRequesterAppeals } from '../api/requesters'
import { AppealTable } from '../components/appeals/AppealTable'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import {
  CATEGORY_LABELS,
  REQUESTER_CATEGORY_LABELS,
  REQUESTER_TYPE_LABELS,
} from '../types/common'

export function RequesterCard() {
  const { id } = useParams()
  const requesterId = Number(id)

  const { data: requester } = useQuery({
    queryKey: ['requester', requesterId],
    queryFn: () => fetchRequester(requesterId),
  })
  const { data: appeals, isLoading } = useQuery({
    queryKey: ['requester-appeals', requesterId],
    queryFn: () => fetchRequesterAppeals(requesterId),
  })

  if (!requester) return <LoadingSpinner label="Загрузка карточки заявителя…" />

  return (
    <div className="space-y-4">
      <Link to="/requesters" className="inline-flex items-center gap-2 text-sm text-navy-300 hover:text-navy-100">
        <ArrowLeft className="h-4 w-4" /> К списку обращавшихся
      </Link>

      <div className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="flex items-center gap-2 text-lg font-semibold text-navy-50">
              {requester.is_repeat_complainant && <UserX className="h-5 w-5 text-risk-high" />}
              {requester.full_name}
            </h1>
            <p className="mt-1 text-sm text-navy-400">
              {REQUESTER_TYPE_LABELS[requester.requester_type] ?? requester.requester_type}
              {requester.affiliation && ` · ${requester.affiliation}`}
            </p>
            <p className="mt-2 inline-block rounded-full border border-border bg-surface px-3 py-1 text-xs text-navy-200">
              {REQUESTER_CATEGORY_LABELS[requester.category] ?? requester.category}
              {requester.repeat_score > 0 && (
                <span className="ml-2 font-mono text-navy-400">скор {requester.repeat_score.toFixed(2)}</span>
              )}
            </p>
            <p className="mt-2 max-w-xl text-[11px] text-navy-500">
              Классификация используется только для внутренней маршрутизации. Каждое обращение
              рассматривается по существу независимо от категории заявителя.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Stat label="Всего" value={requester.total_appeals} />
            <Stat label="Решено" value={requester.resolved_appeals} />
            <Stat label="Отклонено" value={requester.rejected_appeals} />
          </div>
        </div>

        <div className="mt-5 grid gap-4 text-xs text-navy-300 md:grid-cols-3">
          <div>
            <p className="mb-1 uppercase tracking-wider text-navy-500">Активность</p>
            {requester.first_appeal_date && (
              <p>Первое: {format(new Date(requester.first_appeal_date), 'dd.MM.yyyy', { locale: ru })}</p>
            )}
            {requester.last_appeal_date && (
              <p>Последнее: {format(new Date(requester.last_appeal_date), 'dd.MM.yyyy', { locale: ru })}</p>
            )}
            {requester.behavior_stats?.avg_per_month !== undefined && (
              <p>В среднем: {requester.behavior_stats.avg_per_month} обращ./мес</p>
            )}
          </div>
          <div>
            <p className="mb-1 uppercase tracking-wider text-navy-500">Основные темы</p>
            <p>{requester.top_topics.map((t) => CATEGORY_LABELS[t] ?? t).join(', ') || '—'}</p>
          </div>
          <div>
            <p className="mb-1 uppercase tracking-wider text-navy-500">Локации</p>
            <p>{requester.top_regions.join(', ') || '—'}</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="border-b border-border px-4 py-3 text-sm font-semibold text-navy-100">
          История обращений
        </h2>
        {isLoading ? <LoadingSpinner /> : <AppealTable appeals={appeals ?? []} />}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-surface px-4 py-3 text-center">
      <p className="font-mono text-xl font-semibold text-navy-50">{value}</p>
      <p className="text-[10px] uppercase tracking-wider text-navy-400">{label}</p>
    </div>
  )
}

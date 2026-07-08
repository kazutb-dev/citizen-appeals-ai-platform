import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { FilePlus2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchMyAppeals } from '../api/appeals'
import { StatusBadge } from '../components/appeals/StatusBadge'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { CATEGORY_LABELS, STATUS_LABELS, SUBCATEGORY_LABELS } from '../types/common'

export function MyAppeals() {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['my-appeals', { page, status }],
    queryFn: () => fetchMyAppeals({ page, page_size: 20, status: status || undefined }),
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-lg font-semibold text-navy-50">Мои обращения</h1>
          <p className="mt-1 text-sm text-navy-400">История ваших обращений и статусы рассмотрения</p>
        </div>
        <Link to="/submit" className="btn-primary shrink-0">
          <FilePlus2 className="h-4 w-4" /> Подать обращение
        </Link>
      </div>

      <div className="card flex items-center gap-3 p-4">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }} className="input">
          <option value="">Все статусы</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        {data && <span className="text-xs text-navy-400">Всего: {data.total}</span>}
      </div>

      {isLoading ? (
        <LoadingSpinner label="Загрузка обращений…" />
      ) : data?.items.length ? (
        <div className="space-y-3">
          {data.items.map((a) => (
            <Link
              key={a.id}
              to={`/appeal/${a.id}`}
              className="card block p-4 transition hover:border-border-light"
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-navy-400">#{a.id}</span>
                <StatusBadge status={a.status} />
              </div>
              <p className="text-sm font-medium text-navy-100">{a.title}</p>
              <p className="mt-2 text-xs text-navy-400">
                {CATEGORY_LABELS[a.category] ?? a.category}
                {a.subcategory && ` · ${SUBCATEGORY_LABELS[a.subcategory] ?? a.subcategory}`}
                {' · '}
                {format(new Date(a.submitted_at), 'dd MMMM yyyy', { locale: ru })}
              </p>
            </Link>
          ))}
          {totalPages > 1 && (
            <div className="flex items-center justify-end gap-2 text-xs text-navy-400">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-ghost !px-3 !py-1.5">←</button>
              <span className="font-mono">{page} / {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="btn-ghost !px-3 !py-1.5">→</button>
            </div>
          )}
        </div>
      ) : (
        <EmptyState
          title="У вас пока нет обращений"
          hint="Нажмите «Подать обращение», чтобы отправить первый вопрос"
        />
      )}
    </div>
  )
}

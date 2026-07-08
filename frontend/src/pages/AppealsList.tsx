import { Search } from 'lucide-react'
import { useState } from 'react'
import { AppealTable } from '../components/appeals/AppealTable'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useAppeals } from '../hooks/useAppeals'
import { CATEGORY_LABELS, RISK_LABELS, STATUS_LABELS } from '../types/common'

export function AppealsList({ criticalOnly = false }: { criticalOnly?: boolean }) {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [riskLevel, setRiskLevel] = useState(criticalOnly ? 'critical' : '')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const { data, isLoading, isError } = useAppeals({
    page,
    page_size: 20,
    status: status || undefined,
    category: category || undefined,
    risk_level: (criticalOnly ? 'critical' : riskLevel) || undefined,
    search: search || undefined,
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="space-y-4">
      <div className="card flex flex-wrap items-center gap-3 p-4">
        <form
          className="relative min-w-[220px] flex-1"
          onSubmit={(e) => {
            e.preventDefault()
            setSearch(searchInput)
            setPage(1)
          }}
        >
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-navy-400" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Поиск по тексту обращения…"
            className="input w-full pl-9"
          />
        </form>

        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }} className="input">
          <option value="">Все статусы</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>

        <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1) }} className="input">
          <option value="">Все категории</option>
          {Object.entries(CATEGORY_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>

        {!criticalOnly && (
          <select value={riskLevel} onChange={(e) => { setRiskLevel(e.target.value); setPage(1) }} className="input">
            <option value="">Любой риск</option>
            {Object.entries(RISK_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        )}
      </div>

      <div className="card">
        {isLoading ? (
          <LoadingSpinner label="Загрузка обращений…" />
        ) : isError ? (
          <EmptyState title="Ошибка загрузки" hint="Не удалось получить список обращений. Попробуйте обновить страницу." />
        ) : (
          <AppealTable appeals={data?.items ?? []} />
        )}

        {data && data.total > 0 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-navy-400">
            <span>
              Всего: <span className="font-mono text-navy-200">{data.total}</span>
            </span>
            <div className="flex items-center gap-2">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-ghost !px-3 !py-1.5">
                ← Назад
              </button>
              <span className="font-mono">
                {page} / {totalPages}
              </span>
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="btn-ghost !px-3 !py-1.5">
                Вперёд →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

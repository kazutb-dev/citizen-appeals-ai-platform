import { useQuery } from '@tanstack/react-query'
import { Search, UserX } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchRequesters } from '../api/requesters'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { REQUESTER_CATEGORY_LABELS, REQUESTER_TYPE_LABELS } from '../types/common'

export function RequestersPage() {
  const [page, setPage] = useState(1)
  const [category, setCategory] = useState('')
  const [requesterType, setRequesterType] = useState('')
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['requesters', { page, category, requesterType, search }],
    queryFn: () =>
      fetchRequesters({
        page,
        page_size: 20,
        category: category || undefined,
        requester_type: requesterType || undefined,
        search: search || undefined,
      }),
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
            placeholder="Поиск по ФИО…"
            className="input w-full pl-9"
          />
        </form>
        <select value={requesterType} onChange={(e) => { setRequesterType(e.target.value); setPage(1) }} className="input">
          <option value="">Все типы</option>
          {Object.entries(REQUESTER_TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1) }} className="input">
          <option value="">Все категории</option>
          {Object.entries(REQUESTER_CATEGORY_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      <div className="card">
        {isLoading ? (
          <LoadingSpinner label="Загрузка данных…" />
        ) : data?.items.length ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-navy-400">
                <th className="px-4 py-3">ФИО</th>
                <th className="px-4 py-3">Тип</th>
                <th className="px-4 py-3">Регион / организация</th>
                <th className="px-4 py-3">Категория</th>
                <th className="px-4 py-3 text-right">Обращений</th>
                <th className="px-4 py-3 text-right">Решено</th>
                <th className="px-4 py-3 text-right">Скор</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id} className="border-b border-border/50 transition-colors hover:bg-surface-card/60">
                  <td className="px-4 py-3">
                    <Link to={`/requesters/${r.id}`} className="flex items-center gap-2 text-navy-100 hover:text-teal-400">
                      {r.is_repeat_complainant && <UserX className="h-3.5 w-3.5 text-risk-high" />}
                      {r.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-navy-300">
                    {REQUESTER_TYPE_LABELS[r.requester_type] ?? r.requester_type}
                  </td>
                  <td className="px-4 py-3 text-navy-300">{r.affiliation ?? '—'}</td>
                  <td className="px-4 py-3 text-navy-300">
                    {REQUESTER_CATEGORY_LABELS[r.category] ?? r.category}
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-navy-200">{r.total_appeals}</td>
                  <td className="px-4 py-3 text-right font-mono text-navy-300">{r.resolved_appeals}</td>
                  <td className="px-4 py-3 text-right font-mono text-navy-300">
                    {r.repeat_score.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState title="Пациенты не найдены" />
        )}

        {data && data.total > 0 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-navy-400">
            <span>Всего: <span className="font-mono text-navy-200">{data.total}</span></span>
            <div className="flex items-center gap-2">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-ghost !px-3 !py-1.5">←</button>
              <span className="font-mono">{page} / {totalPages}</span>
              <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="btn-ghost !px-3 !py-1.5">→</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

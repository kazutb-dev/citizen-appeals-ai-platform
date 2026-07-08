import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { useState } from 'react'
import { fetchAudit } from '../api/analytics'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

const ACTION_LABELS: Record<string, string> = {
  login: 'Вход в систему',
  logout: 'Выход',
  appeal_created: 'Создано обращение',
  appeal_status_changed: 'Изменён статус',
  appeal_escalated: 'Эскалация',
  appeal_reanalyze: 'Повторный анализ',
  agent_run: 'Запуск агента',
  draft_updated: 'Правка проекта ответа',
  draft_approved: 'Проект ответа утверждён',
  seed_loaded: 'Загрузка демо-данных',
}

export function AuditLog() {
  const [action, setAction] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['audit', { action, page }],
    queryFn: () => fetchAudit({ action: action || undefined, page, page_size: 50 }),
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="space-y-4">
      <div className="card flex items-center gap-3 p-4">
        <select value={action} onChange={(e) => { setAction(e.target.value); setPage(1) }} className="input">
          <option value="">Все действия</option>
          {Object.entries(ACTION_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <p className="text-xs text-navy-400">
          Все значимые действия пользователей и агентов фиксируются и неизменяемы.
        </p>
      </div>

      <div className="card">
        {isLoading ? (
          <LoadingSpinner label="Загрузка журнала…" />
        ) : data?.items.length ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-navy-400">
                <th className="px-4 py-3">Время</th>
                <th className="px-4 py-3">Действие</th>
                <th className="px-4 py-3">Исполнитель</th>
                <th className="px-4 py-3">Объект</th>
                <th className="px-4 py-3">Детали</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((e) => (
                <tr key={e.id} className="border-b border-border/50 hover:bg-surface-card/60">
                  <td className="px-4 py-2.5 font-mono text-xs text-navy-400">
                    {format(new Date(e.created_at), 'dd.MM.yy HH:mm:ss')}
                  </td>
                  <td className="px-4 py-2.5 text-navy-200">{ACTION_LABELS[e.action] ?? e.action}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`font-mono text-xs ${
                        e.actor.startsWith('agent:') ? 'text-teal-400' : 'text-navy-300'
                      }`}
                    >
                      {e.actor}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-navy-400">
                    {e.entity_type}{e.entity_id ? ` #${e.entity_id}` : ''}
                  </td>
                  <td className="max-w-[300px] truncate px-4 py-2.5 text-xs text-navy-500">
                    {Object.keys(e.details).length ? JSON.stringify(e.details) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <EmptyState title="Записей нет" />
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

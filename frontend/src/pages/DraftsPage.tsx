import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { CheckCircle2, Save } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { approveDraft, fetchDrafts, updateDraft } from '../api/drafts'
import type { Draft } from '../api/drafts'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

const DRAFT_STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  reviewed: 'Проверен',
  approved: 'Утверждён',
  sent: 'Отправлен',
}

function DraftRow({ draft }: { draft: Draft }) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState(draft.draft_text)
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['drafts'] })

  const save = useMutation({ mutationFn: () => updateDraft(draft.id, text), onSuccess: invalidate })
  const approve = useMutation({ mutationFn: () => approveDraft(draft.id), onSuccess: invalidate })

  return (
    <div className="card p-4">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center justify-between gap-3 text-left">
        <div>
          <p className="text-sm font-medium text-navy-100">
            {draft.appeal ? draft.appeal.title : `Обращение #${draft.appeal_id}`}
          </p>
          <p className="mt-0.5 text-xs text-navy-400">
            {format(new Date(draft.created_at), 'dd MMM yyyy HH:mm', { locale: ru })} ·
            модель: {draft.generation_model ?? '—'} · уверенность{' '}
            {Math.round(draft.confidence_score * 100)}%
          </p>
        </div>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${
            draft.status === 'approved'
              ? 'border-risk-low/40 bg-risk-low/15 text-risk-low'
              : draft.status === 'reviewed'
                ? 'border-primary/40 bg-teal-400/10 text-teal-400'
                : 'border-slate-500/40 bg-slate-500/15 text-navy-200'
          }`}
        >
          {DRAFT_STATUS_LABELS[draft.status] ?? draft.status}
        </span>
      </button>

      {open && (
        <div className="mt-4 space-y-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={10}
            className="input w-full resize-y text-xs leading-relaxed"
          />
          {draft.legal_references.length > 0 && (
            <div className="text-xs text-navy-400">
              Правовые ссылки: {draft.legal_references
                .map((r) => r.law ?? r.document ?? '')
                .filter(Boolean)
                .join('; ')}
            </div>
          )}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => save.mutate()}
              disabled={save.isPending}
              className="btn-ghost !py-2 text-xs"
            >
              <Save className="h-3.5 w-3.5" /> Сохранить правки
            </button>
            <button
              onClick={() => approve.mutate()}
              disabled={approve.isPending || draft.status === 'approved'}
              className="btn-primary !py-2 text-xs"
            >
              <CheckCircle2 className="h-3.5 w-3.5" /> Утвердить
            </button>
            <Link to={`/appeals/${draft.appeal_id}`} className="btn-ghost !py-2 text-xs">
              Открыть обращение →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export function DraftsPage() {
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['drafts', { status, page }],
    queryFn: () => fetchDrafts({ status: status || undefined, page, page_size: 20 }),
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="space-y-4">
      <div className="card flex items-center gap-3 p-4">
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }} className="input">
          <option value="">Все статусы</option>
          {Object.entries(DRAFT_STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <p className="text-xs text-navy-400">
          Проекты ответов генерирует Агент 4 с опорой на базу знаний (RAG).
          Перед отправкой заявителю проект проверяет и утверждает сотрудник.
        </p>
      </div>

      {isLoading ? (
        <LoadingSpinner label="Загрузка проектов ответов…" />
      ) : data?.items.length ? (
        <div className="space-y-3">
          {data.items.map((d) => (
            <DraftRow key={d.id} draft={d} />
          ))}
          <div className="flex items-center justify-end gap-2 text-xs text-navy-400">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="btn-ghost !px-3 !py-1.5">←</button>
            <span className="font-mono">{page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="btn-ghost !px-3 !py-1.5">→</button>
          </div>
        </div>
      ) : (
        <EmptyState title="Проектов ответов нет" hint="Они появятся после анализа обращений Агентом 4" />
      )}
    </div>
  )
}

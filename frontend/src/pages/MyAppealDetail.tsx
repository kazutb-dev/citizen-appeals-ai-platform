import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { ArrowLeft, CheckCircle2, Circle, Clock, Loader2, Paperclip } from 'lucide-react'
import { useRef } from 'react'
import { Link, useParams } from 'react-router-dom'
import { attachmentUrl, fetchMyAppeal, uploadAttachment } from '../api/appeals'
import { StatusBadge } from '../components/appeals/StatusBadge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { CATEGORY_LABELS, SUBCATEGORY_LABELS } from '../types/common'

const EVENT_LABELS: Record<string, string> = {
  submitted: 'Обращение подано',
  status_changed: 'Статус изменён',
  assigned: 'Назначено подразделение',
  response_approved: 'Получен официальный ответ',
  response_sent: 'Ответ направлен',
  comment: 'Комментарий',
}

// Шаги воркфлоу рассмотрения для прогресс-индикатора
const WORKFLOW = [
  { key: 'submitted', label: 'Подано' },
  { key: 'analysis', label: 'AI-анализ' },
  { key: 'assigned', label: 'Назначен департамент' },
  { key: 'review', label: 'Рассмотрение' },
  { key: 'response', label: 'Ответ' },
  { key: 'closed', label: 'Закрыто' },
]

function workflowStep(status: string, hasResponse: boolean): number {
  if (status === 'resolved' || status === 'rejected' || status === 'duplicate') return 5
  if (hasResponse) return 4
  if (status === 'in_progress' || status === 'escalated' || status === 'pending_review') return 3
  if (status === 'analyzing') return 1
  return 0
}

export function MyAppealDetail() {
  const { id } = useParams()
  const appealId = Number(id)
  const queryClient = useQueryClient()
  const fileInput = useRef<HTMLInputElement>(null)

  const { data: appeal, isLoading } = useQuery({
    queryKey: ['my-appeal', appealId],
    queryFn: () => fetchMyAppeal(appealId),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadAttachment(appealId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-appeal', appealId] }),
  })

  if (isLoading || !appeal) return <LoadingSpinner label="Загрузка обращения…" />

  const step = workflowStep(appeal.status, !!appeal.official_response)

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <Link to="/my-appeals" className="inline-flex items-center gap-2 text-sm text-navy-300 hover:text-navy-100">
        <ArrowLeft className="h-4 w-4" /> К моим обращениям
      </Link>

      {/* Прогресс рассмотрения */}
      <div className="card p-5">
        <div className="flex items-center justify-between">
          {WORKFLOW.map((w, i) => (
            <div key={w.key} className="flex flex-1 items-center">
              <div className="flex flex-col items-center gap-1">
                {i <= step ? (
                  <CheckCircle2 className="h-5 w-5 text-risk-low" />
                ) : (
                  <Circle className="h-5 w-5 text-navy-500" />
                )}
                <span className={`text-[10px] ${i <= step ? 'text-navy-200' : 'text-navy-500'}`}>
                  {w.label}
                </span>
              </div>
              {i < WORKFLOW.length - 1 && (
                <div className={`mx-1 h-px flex-1 ${i < step ? 'bg-risk-low/60' : 'bg-border'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="card p-5">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs text-navy-400">#{appeal.id}</span>
          <StatusBadge status={appeal.status} />
          <span className="ml-auto text-xs text-navy-400">
            {format(new Date(appeal.submitted_at), 'dd MMMM yyyy, HH:mm', { locale: ru })}
          </span>
        </div>
        <h1 className="mb-2 text-base font-semibold text-navy-50">{appeal.title}</h1>
        <p className="mb-3 text-xs text-navy-400">
          {CATEGORY_LABELS[appeal.category] ?? appeal.category}
          {appeal.subcategory && ` · ${SUBCATEGORY_LABELS[appeal.subcategory] ?? appeal.subcategory}`}
          {' · '}{appeal.region}
          {appeal.district && ` · ${appeal.district}`}
        </p>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-navy-200">{appeal.text}</p>

        <div className="mt-4 border-t border-border pt-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-navy-400">Вложения</p>
            <button
              onClick={() => fileInput.current?.click()}
              disabled={uploadMutation.isPending}
              className="btn-ghost !px-3 !py-1.5 text-xs"
            >
              {uploadMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Paperclip className="h-3.5 w-3.5" />}
              Добавить файл
            </button>
            <input
              ref={fileInput}
              type="file"
              className="hidden"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.txt"
              onChange={(e) => e.target.files?.[0] && uploadMutation.mutate(e.target.files[0])}
            />
          </div>
          {appeal.attachments.length ? (
            <ul className="mt-2 space-y-1">
              {appeal.attachments.map((att) => (
                <li key={att.id}>
                  <a
                    href={attachmentUrl(appeal.id, att.id)}
                    className="flex items-center gap-2 text-xs text-teal-400 hover:underline"
                  >
                    <Paperclip className="h-3 w-3" />
                    {att.filename}
                    <span className="text-navy-500">({Math.round(att.size_bytes / 1024)} КБ)</span>
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-xs text-navy-500">Файлы не прикреплены</p>
          )}
        </div>
      </div>

      {/* Рекомендации и сроки */}
      <div className="card p-5 text-sm">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-navy-400">
          Рассмотрение
        </h2>
        <div className="space-y-1.5 text-xs text-navy-300">
          {appeal.responsible_department && (
            <p>Ответственное подразделение: <span className="text-navy-200">{appeal.responsible_department}</span></p>
          )}
          {appeal.expected_response_time && (
            <p className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5" />
              Ориентировочный срок ответа: <span className="text-navy-200">{appeal.expected_response_time}</span>
            </p>
          )}
        </div>
      </div>

      {/* Официальный ответ */}
      {appeal.official_response && (
        <div className="card border-risk-low/40 p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-risk-low">
            <CheckCircle2 className="h-4 w-4" /> Официальный ответ организации
          </h2>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-navy-100">
            {appeal.official_response}
          </p>
        </div>
      )}

      {/* История */}
      <div className="card p-5">
        <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-navy-400">
          История рассмотрения
        </h2>
        <div className="space-y-3">
          {appeal.events.map((event) => (
            <div key={event.id} className="flex gap-3 text-sm">
              <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary/60" />
              <div>
                <p className="text-navy-200">
                  {EVENT_LABELS[event.event_type] ?? event.event_type}
                  {event.details?.to != null && (
                    <span className="text-navy-400"> → {String(event.details.to)}</span>
                  )}
                </p>
                {event.comment && <p className="text-xs text-navy-400">{event.comment}</p>}
                <p className="text-[10px] text-navy-500">
                  {format(new Date(event.created_at), 'dd.MM.yyyy HH:mm', { locale: ru })}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { AlertTriangle, ArrowLeft, CheckCircle2, Copy, Paperclip, RefreshCw, Send } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { attachmentUrl, escalateAppeal, fetchAppealAnalysis, reanalyzeAppeal, updateAppealStatus } from '../api/appeals'
import { AgentResult } from '../components/agents/AgentResult'
import { RiskBadge } from '../components/appeals/RiskBadge'
import { StatusBadge } from '../components/appeals/StatusBadge'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useAppeal } from '../hooks/useAppeals'
import { CATEGORY_LABELS, REQUESTER_CATEGORY_LABELS, SUBCATEGORY_LABELS } from '../types/common'

export function AppealDetail() {
  const { id } = useParams()
  const appealId = Number(id)
  const { data: appeal, isLoading } = useAppeal(appealId)
  const { data: agentAnalysis } = useQuery({
    queryKey: ['appeal-analysis', appealId],
    queryFn: () => fetchAppealAnalysis(appealId),
    enabled: !!appealId,
  })
  const queryClient = useQueryClient()

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['appeal', appealId] })
    queryClient.invalidateQueries({ queryKey: ['appeals'] })
  }

  const statusMutation = useMutation({
    mutationFn: (status: string) => updateAppealStatus(appealId, status),
    onSuccess: invalidate,
  })
  const escalateMutation = useMutation({
    mutationFn: () => escalateAppeal(appealId),
    onSuccess: invalidate,
  })
  const reanalyzeMutation = useMutation({
    mutationFn: () => reanalyzeAppeal(appealId),
    onSuccess: invalidate,
  })

  if (isLoading || !appeal) return <LoadingSpinner label="Загрузка обращения…" />

  const agentPayloads: [string, Record<string, any>][] = [
    ['agent1', {
      risk_level: appeal.risk_level,
      risk_score: appeal.risk_score,
      risk_reasons: appeal.risk_reasons,
      tags: appeal.tags ?? [],
      escalate: appeal.is_escalated,
      escalation_level: appeal.escalation_level,
    }],
    ['agent3', {
      is_duplicate: appeal.is_duplicate,
      duplicate_of_id: appeal.duplicate_of_id,
      score: appeal.duplicate_score,
      reason: appeal.duplicate_of_id ? `Совпадение с обращением #${appeal.duplicate_of_id}` : '',
    }],
    ['agent2', {
      is_campaign: appeal.is_campaign,
      score: appeal.campaign_score,
      cluster_id: appeal.campaign_cluster_id,
    }],
    ['agent5', {
      category: appeal.requester?.category ?? 'normal',
      score: appeal.from_repeat_complainant ? 0.7 : 0,
    }],
    ['agent4', appeal.draft_response
      ? {
          text: appeal.draft_response.draft_text,
          confidence: appeal.draft_response.confidence_score,
          legal_refs: appeal.draft_response.legal_references,
        }
      : {}],
    // Агенты 6–8: лекарственное обеспечение, качество, санэпид — данные из журнала аудита
    ...(agentAnalysis
      ? (['agent6', 'agent7', 'agent8'] as const)
          .filter((k) => k in agentAnalysis)
          .map((k) => [k, agentAnalysis[k]] as [string, Record<string, any>])
      : []),
  ]

  return (
    <div className="space-y-4">
      <Link to="/appeals" className="inline-flex items-center gap-2 text-sm text-navy-300 hover:text-navy-100">
        <ArrowLeft className="h-4 w-4" /> К списку обращений
      </Link>

      <div className="grid gap-6 xl:grid-cols-[35%_1fr_25%]">
        {/* Левая колонка: текст обращения */}
        <div className="space-y-4">
          <div className="card p-5">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-navy-400">#{appeal.id}</span>
              {appeal.external_id && (
                <span className="rounded bg-surface-card px-2 py-0.5 font-mono text-[10px] text-navy-300">
                  ID: {appeal.external_id}
                </span>
              )}
              <RiskBadge level={appeal.risk_level} />
              <StatusBadge status={appeal.status} />
            </div>
            <h1 className="mb-3 text-base font-semibold leading-snug text-navy-50">{appeal.title}</h1>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-navy-200">{appeal.text}</p>

            {appeal.attachments.length > 0 && (
              <div className="mt-4 space-y-1.5 border-t border-border pt-3">
                {appeal.attachments.map((att) => (
                  <a
                    key={att.id}
                    href={attachmentUrl(appeal.id, att.id)}
                    className="flex items-center gap-2 text-xs text-teal-400 hover:underline"
                  >
                    <Paperclip className="h-3.5 w-3.5" />
                    {att.filename}
                    <span className="text-navy-400">({Math.round(att.size_bytes / 1024)} КБ)</span>
                  </a>
                ))}
              </div>
            )}
          </div>

          <div className="card space-y-2 p-5 text-sm">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-navy-400">Метаданные</h2>
            <Row label="Категория" value={CATEGORY_LABELS[appeal.category] ?? appeal.category} />
            {appeal.subcategory && (
              <Row label="Подкатегория" value={SUBCATEGORY_LABELS[appeal.subcategory] ?? appeal.subcategory} />
            )}
            <Row label="Локация" value={appeal.location_name || appeal.region} />
            {appeal.district && <Row label="Аудитория / комната" value={appeal.district} />}
            <Row
              label="Источник"
              value={
                ({
                  portal: 'Портал',
                  eotinish: 'E-Өтініш',
                  ikomek: 'iKomek',
                  crm: 'CRM',
                  damumed: 'Damumed',
                  telegram: 'Telegram',
                  instagram: 'Instagram',
                  operator: 'Оператор',
                } as Record<string, string>)[appeal.source_channel ?? ''] ??
                (appeal.source_channel || '—')
              }
            />
            {appeal.latitude != null && appeal.longitude != null && (
              <Row
                label="Координаты"
                value={`${appeal.latitude.toFixed(5)}, ${appeal.longitude.toFixed(5)}`}
              />
            )}
            <Row label="Подано" value={format(new Date(appeal.submitted_at), 'dd MMMM yyyy, HH:mm', { locale: ru })} />
            {appeal.analyzed_at && (
              <Row label="Проанализировано ИИ" value={format(new Date(appeal.analyzed_at), 'dd.MM.yyyy HH:mm')} />
            )}
            {appeal.resolved_at && (
              <Row label="Решено" value={format(new Date(appeal.resolved_at), 'dd.MM.yyyy HH:mm')} />
            )}
            {appeal.escalated_at && (
              <Row label="Эскалировано" value={format(new Date(appeal.escalated_at), 'dd.MM.yyyy HH:mm')} />
            )}
          </div>
        </div>

        {/* Центральная колонка: результаты агентов */}
        <div className="space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-navy-400">
            Результаты анализа агентов
          </h2>
          {agentPayloads.map(([key, payload]) => (
            <AgentResult key={key} agentKey={key} payload={payload} />
          ))}
        </div>

        {/* Правая колонка: действия */}
        <div className="space-y-4">
          <div className="card space-y-2.5 p-4">
            <h2 className="mb-1 text-xs font-semibold uppercase tracking-wider text-navy-400">Действия</h2>
            <button
              onClick={() => escalateMutation.mutate()}
              disabled={appeal.is_escalated || escalateMutation.isPending}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-risk-critical px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700 disabled:opacity-40"
            >
              <AlertTriangle className="h-4 w-4" />
              {appeal.is_escalated ? 'Эскалировано' : 'Эскалировать'}
            </button>
            <button onClick={() => statusMutation.mutate('in_progress')} className="btn-primary w-full justify-center">
              <Send className="h-4 w-4" /> Направить в департамент
            </button>
            <button onClick={() => statusMutation.mutate('resolved')} className="btn-ghost w-full justify-center">
              <CheckCircle2 className="h-4 w-4" /> Утвердить ответ
            </button>
            <button onClick={() => statusMutation.mutate('duplicate')} className="btn-ghost w-full justify-center">
              <Copy className="h-4 w-4" /> Отметить дубликатом
            </button>
            <button
              onClick={() => reanalyzeMutation.mutate()}
              disabled={reanalyzeMutation.isPending}
              className="btn-ghost w-full justify-center"
            >
              <RefreshCw className={`h-4 w-4 ${reanalyzeMutation.isPending ? 'animate-spin' : ''}`} />
              Повторный анализ ИИ
            </button>
            {reanalyzeMutation.isSuccess && (
              <p className="text-center text-[11px] text-teal-400">Анализ поставлен в очередь воркера</p>
            )}
          </div>

          {appeal.requester && (
            <Link to={`/requesters/${appeal.requester.id}`} className="card block p-4 transition hover:border-border-light">
              <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-navy-400">Заявитель</h2>
              <p className="text-sm font-medium text-navy-100">{appeal.requester.full_name}</p>
              <p className="mt-1 text-xs text-navy-400">
                {appeal.requester.affiliation ?? appeal.requester.region} ·{' '}
                {REQUESTER_CATEGORY_LABELS[appeal.requester.category] ?? appeal.requester.category}
              </p>
              <p className="mt-2 text-xs text-teal-400">Карточка заявителя →</p>
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-navy-400">{label}</span>
      <span className="text-right text-navy-200">{value}</span>
    </div>
  )
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import {
  Bot,
  CheckCircle2,
  ExternalLink,
  FileText,
  Loader2,
  Pencil,
  Plug,
  RefreshCw,
  Share2,
  Trash2,
  Upload,
  Users,
  XCircle,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  createSocialSource,
  deleteKnowledge,
  deleteSocialSource,
  fetchAgentSettings,
  fetchIntegrations,
  fetchKnowledge,
  fetchSocialSources,
  fetchUsers,
  instagramHealthCheck,
  instagramOauthExchange,
  instagramOauthUrl,
  pollSocialSource,
  reprocessKnowledge,
  updateAgentSetting,
  updateInstagram,
  updateSocialSource,
  updateUser,
  uploadKnowledge,
} from '../api/admin'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import type { AgentSetting, SocialSource } from '../types/admin'
import { DOC_TYPE_LABELS, SOURCE_STATUS_LABELS } from '../types/admin'
import { PLATFORM_LABELS } from '../types/social'

const TABS = [
  { key: 'agents', label: 'AI-агенты', icon: Bot },
  { key: 'sources', label: 'Социальные источники', icon: Share2 },
  { key: 'integrations', label: 'Интеграции', icon: Plug },
  { key: 'knowledge', label: 'База знаний', icon: FileText },
  { key: 'users', label: 'Пользователи и роли', icon: Users },
]

// ============ AI-агенты: включение, пороги, промпты ============

function AgentRow({ agent }: { agent: AgentSetting }) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [prompt, setPrompt] = useState(agent.prompt_template ?? '')
  const [configText, setConfigText] = useState(JSON.stringify(agent.config ?? {}, null, 2))
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: (payload: Parameters<typeof updateAgentSetting>[1]) =>
      updateAgentSetting(agent.agent_key, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-agents'] })
      setEditing(false)
      setError('')
    },
  })

  const save = () => {
    let config: Record<string, unknown> | undefined
    try {
      config = configText.trim() ? JSON.parse(configText) : {}
    } catch {
      setError('Конфигурация должна быть валидным JSON')
      return
    }
    mutation.mutate({ prompt_template: prompt, config })
  }

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="flex items-center gap-2 text-sm font-semibold text-navy-100">
            <span className="font-mono text-xs text-navy-400">{agent.agent_key}</span>
            {agent.display_name}
          </h3>
          {agent.description && <p className="mt-1 max-w-2xl text-xs text-navy-400">{agent.description}</p>}
          {agent.prompt_template && (
            <span className="mt-2 inline-block rounded bg-accent/10 px-2 py-0.5 text-[10px] text-teal-400">
              Кастомный промпт
            </span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button onClick={() => setEditing(!editing)} className="btn-ghost !px-3 !py-1.5 text-xs">
            <Pencil className="h-3.5 w-3.5" /> Настроить
          </button>
          <button
            onClick={() => mutation.mutate({ is_enabled: !agent.is_enabled })}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
              agent.is_enabled
                ? 'bg-risk-low/15 text-risk-low hover:bg-risk-low/25'
                : 'bg-slate-600/20 text-navy-300 hover:bg-slate-600/30'
            }`}
          >
            {agent.is_enabled ? 'Включён' : 'Выключен'}
          </button>
        </div>
      </div>

      {editing && (
        <div className="mt-4 space-y-3 border-t border-border pt-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">
              Промпт (пусто — использовать промпт по умолчанию; плейсхолдеры вида {'{appeal_text}'} обязательны)
            </label>
            <textarea
              rows={8}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="input w-full resize-y font-mono text-xs"
              placeholder="Промпт по умолчанию из кода агента"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">
              Конфигурация (JSON): пороги, ключевые слова, правила эскалации
            </label>
            <textarea
              rows={5}
              value={configText}
              onChange={(e) => setConfigText(e.target.value)}
              className="input w-full resize-y font-mono text-xs"
            />
          </div>
          {error && <p className="text-xs text-risk-critical">{error}</p>}
          <button onClick={save} disabled={mutation.isPending} className="btn-primary text-xs">
            {mutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Сохранить
          </button>
        </div>
      )}
    </div>
  )
}

function AgentsTab() {
  const { data, isLoading } = useQuery({ queryKey: ['admin-agents'], queryFn: fetchAgentSettings })
  if (isLoading) return <LoadingSpinner label="Загрузка агентов…" />
  return (
    <div className="space-y-4">
      {data?.map((agent) => <AgentRow key={agent.agent_key} agent={agent} />)}
    </div>
  )
}

// ============ Социальные источники ============

const EMPTY_SOURCE = {
  name: '',
  platform: 'telegram',
  url: '',
  polling_interval_minutes: 30,
  is_enabled: true,
  credentialsText: '',
}

function SourcesTab() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['admin-sources'], queryFn: fetchSocialSources })
  const [form, setForm] = useState(EMPTY_SOURCE)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-sources'] })

  const saveMutation = useMutation({
    mutationFn: async () => {
      let credentials: Record<string, string> = {}
      if (form.credentialsText.trim()) {
        credentials = JSON.parse(form.credentialsText)
      }
      const payload = {
        name: form.name,
        platform: form.platform,
        url: form.url || undefined,
        credentials,
        polling_interval_minutes: form.polling_interval_minutes,
        is_enabled: form.is_enabled,
      }
      return editingId ? updateSocialSource(editingId, payload) : createSocialSource(payload)
    },
    onSuccess: () => {
      invalidate()
      setForm(EMPTY_SOURCE)
      setEditingId(null)
      setError('')
    },
    onError: (err: any) => setError(err?.response?.data?.detail ?? 'Ошибка сохранения (учётные данные — JSON)'),
  })

  const deleteMutation = useMutation({ mutationFn: deleteSocialSource, onSuccess: invalidate })
  const toggleMutation = useMutation({
    mutationFn: (s: SocialSource) => updateSocialSource(s.id, { is_enabled: !s.is_enabled }),
    onSuccess: invalidate,
  })
  const pollMutation = useMutation({ mutationFn: pollSocialSource, onSuccess: invalidate })

  const startEdit = (s: SocialSource) => {
    setEditingId(s.id)
    setForm({
      name: s.name,
      platform: s.platform,
      url: s.url ?? '',
      polling_interval_minutes: s.polling_interval_minutes,
      is_enabled: s.is_enabled,
      credentialsText: '',
    })
  }

  return (
    <div className="space-y-4">
      <form
        onSubmit={(e) => { e.preventDefault(); saveMutation.mutate() }}
        className="card space-y-3 p-5"
      >
        <h3 className="text-sm font-semibold text-navy-100">
          {editingId ? `Источник #${editingId}` : 'Добавить источник'}
        </h3>
        <div className="grid gap-3 md:grid-cols-2">
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" placeholder="Название источника" />
          <select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })} className="input" disabled={!!editingId}>
            {Object.entries(PLATFORM_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
          <input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="input" placeholder="URL (https://t.me/…, instagram.com/…)" />
          <div className="flex items-center gap-3">
            <label className="text-xs text-navy-300">Интервал опроса, мин</label>
            <input
              type="number"
              min={5}
              max={1440}
              value={form.polling_interval_minutes}
              onChange={(e) => setForm({ ...form, polling_interval_minutes: Number(e.target.value) })}
              className="input w-24"
            />
            <label className="ml-auto flex items-center gap-2 text-xs text-navy-300">
              <input
                type="checkbox"
                checked={form.is_enabled}
                onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })}
              />
              Включён
            </label>
          </div>
        </div>
        <input
          value={form.credentialsText}
          onChange={(e) => setForm({ ...form, credentialsText: e.target.value })}
          className="input w-full font-mono text-xs"
          placeholder='Учётные данные платформы (JSON), например {"access_token": "…"} — для VK, Facebook, TikTok, X'
        />
        {error && <p className="text-xs text-risk-critical">{error}</p>}
        <div className="flex gap-2">
          <button type="submit" disabled={saveMutation.isPending} className="btn-primary text-xs">
            {saveMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            {editingId ? 'Сохранить' : 'Добавить'}
          </button>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(null); setForm(EMPTY_SOURCE) }} className="btn-ghost text-xs">
              Отмена
            </button>
          )}
        </div>
      </form>

      {isLoading ? (
        <LoadingSpinner />
      ) : data?.length ? (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-navy-400">
                <th className="px-4 py-3">Источник</th>
                <th className="px-4 py-3">Платформа</th>
                <th className="px-4 py-3">Интервал</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3">Последний опрос</th>
                <th className="px-4 py-3 text-right">Действия</th>
              </tr>
            </thead>
            <tbody>
              {data.map((s) => (
                <tr key={s.id} className="border-b border-border/50">
                  <td className="px-4 py-3">
                    <p className="text-navy-100">{s.name}</p>
                    {s.url && <p className="truncate text-[11px] text-navy-500">{s.url}</p>}
                    {s.last_error && <p className="mt-1 max-w-sm text-[11px] text-risk-high">{s.last_error}</p>}
                  </td>
                  <td className="px-4 py-3 text-navy-300">{PLATFORM_LABELS[s.platform] ?? s.platform}</td>
                  <td className="px-4 py-3 font-mono text-xs text-navy-300">{s.polling_interval_minutes} мин</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs ${s.last_status === 'ok' ? 'text-risk-low' : s.last_status === 'error' ? 'text-risk-critical' : 'text-navy-300'}`}>
                      {SOURCE_STATUS_LABELS[s.last_status] ?? s.last_status}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-navy-400">
                    {s.last_polled_at ? format(new Date(s.last_polled_at), 'dd.MM HH:mm') : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1.5">
                      <button title="Опросить сейчас" onClick={() => pollMutation.mutate(s.id)} className="btn-ghost !p-2">
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                      <button title="Редактировать" onClick={() => startEdit(s)} className="btn-ghost !p-2">
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        title={s.is_enabled ? 'Отключить' : 'Включить'}
                        onClick={() => toggleMutation.mutate(s)}
                        className="btn-ghost !p-2"
                      >
                        {s.is_enabled ? <CheckCircle2 className="h-3.5 w-3.5 text-risk-low" /> : <XCircle className="h-3.5 w-3.5 text-navy-400" />}
                      </button>
                      <button
                        title="Удалить"
                        onClick={() => {
                          if (window.confirm(`Удалить источник «${s.name}»?`)) deleteMutation.mutate(s.id)
                        }}
                        className="btn-ghost !p-2 hover:text-risk-critical"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="Источники не добавлены" />
      )}
    </div>
  )
}

// ============ Интеграции (Instagram Graph API) ============

function IntegrationsTab() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const { data, isLoading } = useQuery({ queryKey: ['admin-integrations'], queryFn: fetchIntegrations })
  const [form, setForm] = useState({ app_id: '', business_account_id: '', app_secret: '', access_token: '' })
  const [message, setMessage] = useState('')

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-integrations'] })

  const saveMutation = useMutation({
    mutationFn: () =>
      updateInstagram({
        app_id: form.app_id || undefined,
        business_account_id: form.business_account_id || undefined,
        app_secret: form.app_secret || undefined,
        access_token: form.access_token || undefined,
      }),
    onSuccess: () => { invalidate(); setMessage('Сохранено'); setForm({ ...form, app_secret: '', access_token: '' }) },
  })
  const healthMutation = useMutation({ mutationFn: instagramHealthCheck, onSuccess: invalidate })
  const oauthMutation = useMutation({
    mutationFn: instagramOauthUrl,
    onSuccess: ({ oauth_url }) => { window.location.href = oauth_url },
    onError: (err: any) => setMessage(err?.response?.data?.detail ?? 'Сначала укажите App ID'),
  })
  const exchangeMutation = useMutation({
    mutationFn: ({ code, state }: { code: string; state: string }) => instagramOauthExchange(code, state),
    onSuccess: () => { invalidate(); setMessage('Instagram подключён через OAuth'); setSearchParams({}) },
    onError: (err: any) => { setMessage(err?.response?.data?.detail ?? 'Ошибка обмена кода'); setSearchParams({}) },
  })

  // Возврат из OAuth: ?code=…&state=… на этой же странице
  const code = searchParams.get('code')
  const state = searchParams.get('state')
  useEffect(() => {
    if (code && state && !exchangeMutation.isPending) {
      exchangeMutation.mutate({ code, state })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, state])

  if (isLoading) return <LoadingSpinner />
  const instagram = data?.find((i) => i.provider === 'instagram')

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-navy-100">Instagram Graph API</h3>
            <p className="mt-1 text-xs text-navy-400">
              Основная интеграция: комментарии, упоминания, сообщения, статистика профиля.
              Логин/пароль и sessionid не используются; публичный парсинг — только запасной вариант.
            </p>
          </div>
          <span
            className={`rounded-full border px-3 py-1 text-xs ${
              instagram?.status === 'connected'
                ? 'border-risk-low/40 bg-risk-low/10 text-risk-low'
                : instagram?.status === 'error'
                  ? 'border-risk-critical/40 bg-risk-critical/10 text-risk-critical'
                  : 'border-slate-500/40 bg-slate-500/10 text-navy-300'
            }`}
          >
            {instagram?.status === 'connected' ? 'Подключено'
              : instagram?.status === 'error' ? 'Ошибка'
              : instagram?.status === 'configured' ? 'Настроено, не подключено'
              : 'Не настроено'}
          </span>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs text-navy-300">App ID</label>
            <input
              value={form.app_id}
              onChange={(e) => setForm({ ...form, app_id: e.target.value })}
              className="input w-full font-mono text-xs"
              placeholder={instagram?.config?.app_id ?? 'ID приложения Meta'}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-navy-300">Business Account ID</label>
            <input
              value={form.business_account_id}
              onChange={(e) => setForm({ ...form, business_account_id: e.target.value })}
              className="input w-full font-mono text-xs"
              placeholder={instagram?.config?.business_account_id ?? 'ID бизнес-аккаунта Instagram'}
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-navy-300">
              App Secret {instagram?.secrets_masked?.app_secret && `(сохранён: ${instagram.secrets_masked.app_secret})`}
            </label>
            <input
              type="password"
              value={form.app_secret}
              onChange={(e) => setForm({ ...form, app_secret: e.target.value })}
              className="input w-full font-mono text-xs"
              placeholder="оставьте пустым, чтобы не менять"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs text-navy-300">
              Access Token {instagram?.secrets_masked?.access_token && `(сохранён: ${instagram.secrets_masked.access_token})`}
            </label>
            <input
              type="password"
              value={form.access_token}
              onChange={(e) => setForm({ ...form, access_token: e.target.value })}
              className="input w-full font-mono text-xs"
              placeholder="заполняется автоматически через OAuth"
            />
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending} className="btn-primary text-xs">
            {saveMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Сохранить
          </button>
          <button onClick={() => oauthMutation.mutate()} disabled={oauthMutation.isPending} className="btn-ghost text-xs">
            <ExternalLink className="h-3.5 w-3.5" /> Подключить через OAuth
          </button>
          <button onClick={() => healthMutation.mutate()} disabled={healthMutation.isPending} className="btn-ghost text-xs">
            {healthMutation.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
            Проверка соединения
          </button>
          {message && <span className="text-xs text-teal-400">{message}</span>}
        </div>

        {(instagram?.last_health_status || instagram?.token_expires_at) && (
          <div className="mt-4 space-y-1 border-t border-border pt-3 text-xs text-navy-400">
            {instagram.last_health_status && (
              <p>
                Последняя проверка:{' '}
                <span className={instagram.last_health_status.startsWith('OK') ? 'text-risk-low' : 'text-risk-high'}>
                  {instagram.last_health_status}
                </span>
                {instagram.last_health_check_at &&
                  ` (${format(new Date(instagram.last_health_check_at), 'dd.MM.yyyy HH:mm')})`}
              </p>
            )}
            {instagram.token_expires_at && (
              <p>Токен действителен до: {format(new Date(instagram.token_expires_at), 'dd.MM.yyyy')}</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ============ База знаний ============

function KnowledgeTab() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['admin-knowledge'], queryFn: fetchKnowledge })
  const [title, setTitle] = useState('')
  const [docType, setDocType] = useState('regulation')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['admin-knowledge'] })

  const uploadMutation = useMutation({
    mutationFn: () => uploadKnowledge(file!, { title, doc_type: docType }),
    onSuccess: () => { invalidate(); setTitle(''); setFile(null); setError('') },
    onError: (err: any) => setError(err?.response?.data?.detail ?? 'Ошибка загрузки'),
  })
  const deleteMutation = useMutation({ mutationFn: deleteKnowledge, onSuccess: invalidate })
  const reprocessMutation = useMutation({ mutationFn: reprocessKnowledge, onSuccess: invalidate })

  return (
    <div className="space-y-4">
      <form
        onSubmit={(e) => { e.preventDefault(); if (file) uploadMutation.mutate() }}
        className="card space-y-3 p-5"
      >
        <h3 className="text-sm font-semibold text-navy-100">Загрузить документ</h3>
        <p className="text-xs text-navy-400">
          Положения, политики, правила, клинические протоколы — Агент 4 использует их через RAG
          при подготовке официальных ответов. Форматы: PDF, DOCX, TXT, MD.
        </p>
        <div className="grid gap-3 md:grid-cols-3">
          <input required minLength={3} value={title} onChange={(e) => setTitle(e.target.value)} className="input md:col-span-2" placeholder="Название документа" />
          <select value={docType} onChange={(e) => setDocType(e.target.value)} className="input">
            {Object.entries(DOC_TYPE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border px-4 py-2 text-xs text-navy-300 transition hover:border-border-light hover:text-navy-100">
            <Upload className="h-3.5 w-3.5" />
            {file ? file.name : 'Выбрать файл'}
            <input
              type="file"
              className="hidden"
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <button type="submit" disabled={!file || uploadMutation.isPending} className="btn-primary text-xs">
            {uploadMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Загрузить
          </button>
          {error && <span className="text-xs text-risk-critical">{error}</span>}
        </div>
      </form>

      {isLoading ? (
        <LoadingSpinner />
      ) : data?.length ? (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-navy-400">
                <th className="px-4 py-3">Документ</th>
                <th className="px-4 py-3">Тип</th>
                <th className="px-4 py-3">Статус</th>
                <th className="px-4 py-3 text-right">Фрагментов</th>
                <th className="px-4 py-3">Загружен</th>
                <th className="px-4 py-3 text-right">Действия</th>
              </tr>
            </thead>
            <tbody>
              {data.map((doc) => (
                <tr key={doc.id} className="border-b border-border/50">
                  <td className="px-4 py-3">
                    <p className="text-navy-100">{doc.title}</p>
                    {doc.filename && <p className="text-[11px] text-navy-500">{doc.filename}</p>}
                    {doc.error && <p className="mt-1 max-w-sm text-[11px] text-risk-critical">{doc.error}</p>}
                  </td>
                  <td className="px-4 py-3 text-navy-300">{DOC_TYPE_LABELS[doc.doc_type] ?? doc.doc_type}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs ${doc.status === 'ready' ? 'text-risk-low' : doc.status === 'failed' ? 'text-risk-critical' : 'text-teal-400'}`}>
                      {doc.status === 'ready' ? 'Готов' : doc.status === 'failed' ? 'Ошибка' : 'Обработка…'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-navy-300">{doc.chunk_count}</td>
                  <td className="px-4 py-3 font-mono text-xs text-navy-400">
                    {format(new Date(doc.created_at), 'dd.MM.yyyy')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1.5">
                      <button title="Переобработать" onClick={() => reprocessMutation.mutate(doc.id)} className="btn-ghost !p-2">
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                      <button
                        title="Удалить"
                        onClick={() => {
                          if (window.confirm(`Удалить документ «${doc.title}»?`)) deleteMutation.mutate(doc.id)
                        }}
                        className="btn-ghost !p-2 hover:text-risk-critical"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState title="База знаний пуста" hint="Загрузите внутренние документы организации" />
      )}
    </div>
  )
}

// ============ Пользователи и роли ============

const ROLE_LABELS: Record<string, string> = {
  admin: 'Администратор',
  analyst: 'Аналитик',
  operator: 'Оператор',
  viewer: 'Наблюдатель',
  requester: 'Заявитель (портал)',
}

function UsersTab() {
  const queryClient = useQueryClient()
  const [roleFilter, setRoleFilter] = useState('')
  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', roleFilter],
    queryFn: () => fetchUsers(roleFilter || undefined),
  })
  const mutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Parameters<typeof updateUser>[1] }) =>
      updateUser(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  })

  return (
    <div className="space-y-4">
      <div className="card flex items-center gap-3 p-4">
        <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="input">
          <option value="">Все роли</option>
          {Object.entries(ROLE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs uppercase tracking-wider text-navy-400">
                <th className="px-4 py-3">Пользователь</th>
                <th className="px-4 py-3">Роль</th>
                <th className="px-4 py-3">Должность</th>
                <th className="px-4 py-3">Статус</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((u) => (
                <tr key={u.id} className="border-b border-border/50">
                  <td className="px-4 py-3">
                    <p className="text-navy-100">{u.full_name}</p>
                    <p className="text-[11px] text-navy-500">{u.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      onChange={(e) => mutation.mutate({ id: u.id, payload: { role: e.target.value } })}
                      className="input !py-1 text-xs"
                    >
                      {Object.entries(ROLE_LABELS).map(([k, v]) => (
                        <option key={k} value={k}>{v}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3 text-xs text-navy-300">{u.position ?? '—'}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => mutation.mutate({ id: u.id, payload: { is_active: !u.is_active } })}
                      className={`rounded-lg px-3 py-1 text-xs transition ${
                        u.is_active
                          ? 'bg-risk-low/15 text-risk-low'
                          : 'bg-slate-600/20 text-navy-400'
                      }`}
                    >
                      {u.is_active ? 'Активен' : 'Деактивирован'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ============ Страница ============

export function AdminPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  // Возврат из Instagram OAuth содержит ?code= — открываем вкладку интеграций
  const initialTab = searchParams.get('code') ? 'integrations' : searchParams.get('tab') ?? 'agents'
  const [tab, setTab] = useState(initialTab)

  const select = (key: string) => {
    setTab(key)
    if (!searchParams.get('code')) setSearchParams({ tab: key })
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => select(key)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm transition ${
              tab === key ? 'bg-teal-400/12 text-teal-400' : 'text-navy-300 hover:text-navy-100'
            }`}
          >
            <Icon className="h-4 w-4" /> {label}
          </button>
        ))}
      </div>

      {tab === 'agents' && <AgentsTab />}
      {tab === 'sources' && <SourcesTab />}
      {tab === 'integrations' && <IntegrationsTab />}
      {tab === 'knowledge' && <KnowledgeTab />}
      {tab === 'users' && <UsersTab />}
    </div>
  )
}

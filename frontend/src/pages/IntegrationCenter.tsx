import { useMutation, useQuery } from '@tanstack/react-query'
import { CheckCircle2, Inbox, Plug } from 'lucide-react'
import { useState } from 'react'
import {
  fetchIntegrationCatalog,
  fetchIntegrationSample,
  testIntegration,
} from '../api/integrations'
import type { IntegrationMessage } from '../api/integrations'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useAuth } from '../hooks/useAuth'

const KIND_LABELS: Record<string, string> = {
  inbound_appeals: 'Приём обращений',
  ehr: 'МИС / ЭМК',
  interop: 'Интероперабельность',
  messaging: 'Уведомления',
  api: 'API',
}

export function IntegrationCenter() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const { data: providers } = useQuery({
    queryKey: ['integrations-catalog'],
    queryFn: fetchIntegrationCatalog,
  })
  const [sampleKey, setSampleKey] = useState<string | null>(null)
  const [messages, setMessages] = useState<IntegrationMessage[]>([])
  const [testResult, setTestResult] = useState<Record<string, string>>({})

  const sample = useMutation({
    mutationFn: (key: string) => fetchIntegrationSample(key, 5),
    onSuccess: (data, key) => {
      setSampleKey(key)
      setMessages(data)
    },
  })
  const test = useMutation({
    mutationFn: (key: string) => testIntegration(key),
    onSuccess: (data, key) => setTestResult((prev) => ({ ...prev, [key]: data.message })),
  })

  if (!providers) return <LoadingSpinner label="Загрузка интеграций…" />

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">Центр интеграций</h1>
        <p className="text-xs text-navy-400">
          Единый приём обращений из разрозненных систем (iKomek, CRM, E-Otinish, Damumed, FHIR/HL7) — демо-адаптеры
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {providers.map((p) => (
          <div key={p.key} className="card flex flex-col gap-3 p-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <Plug className="h-4 w-4 text-teal-400" />
                <span className="text-sm font-semibold text-navy-100">{p.name}</span>
              </div>
              <span className="rounded-pill bg-surface px-2 py-0.5 text-[10px] uppercase text-navy-400">
                {p.mode}
              </span>
            </div>
            <p className="text-xs text-navy-400">{p.description}</p>
            <div className="flex flex-wrap gap-1">
              <span className="rounded-pill bg-teal-400/10 px-2 py-0.5 text-[10px] text-teal-300">
                {KIND_LABELS[p.kind] ?? p.kind}
              </span>
              <span className="rounded-pill bg-surface px-2 py-0.5 text-[10px] text-navy-400">
                {p.direction}
              </span>
            </div>
            <div className="mt-auto flex gap-2">
              {isAdmin && (
                <button
                  onClick={() => test.mutate(p.key)}
                  className="btn-ghost !px-3 !py-1.5 text-xs"
                >
                  <CheckCircle2 className="h-3.5 w-3.5" /> Тест
                </button>
              )}
              {(p.direction === 'inbound' || p.direction === 'bidirectional') && (
                <button
                  onClick={() => sample.mutate(p.key)}
                  className="btn-ghost !px-3 !py-1.5 text-xs"
                >
                  <Inbox className="h-3.5 w-3.5" /> Приём
                </button>
              )}
            </div>
            {testResult[p.key] && <p className="text-[11px] text-risk-low">{testResult[p.key]}</p>}
          </div>
        ))}
      </div>

      {sampleKey && (
        <div className="card p-5">
          <h2 className="mb-3 text-sm font-semibold text-navy-100">
            Входящие сообщения · {sampleKey}
          </h2>
          <div className="space-y-3">
            {messages.length ? (
              messages.map((m) => (
                <div key={m.external_id} className="rounded-lg border border-border bg-surface p-3">
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="font-medium text-navy-100">{m.author}</span>
                    <span className="text-navy-500">
                      {new Date(m.received_at).toLocaleString('ru-RU')}
                    </span>
                  </div>
                  <p className="text-sm text-navy-200">{m.text}</p>
                  {m.category_hint && (
                    <span className="mt-1 inline-block rounded-pill bg-teal-400/10 px-2 py-0.5 text-[10px] text-teal-300">
                      {m.category_hint}
                    </span>
                  )}
                </div>
              ))
            ) : (
              <p className="text-xs text-navy-400">Нет демо-сообщений для этого канала.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

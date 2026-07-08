import { useQuery } from '@tanstack/react-query'
import { Boxes, Cpu, Database, Layers, Radio, RefreshCw, Server } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { fetchSystemHealth } from '../api/monitoring'
import type { ComponentHealth } from '../api/monitoring'
import { LoadingSpinner } from '../components/common/LoadingSpinner'

const STATUS_TONE: Record<string, string> = {
  ok: 'text-risk-low border-risk-low/40',
  enabled: 'text-risk-low border-risk-low/40',
  configured: 'text-teal-300 border-teal-400/40',
  disabled: 'text-navy-400 border-border',
  not_configured: 'text-risk-medium border-risk-medium/40',
  unreachable: 'text-risk-high border-risk-high/40',
  error: 'text-risk-critical border-risk-critical/40',
  unknown: 'text-navy-400 border-border',
}

function HealthCard({ title, icon: Icon, c }: { title: string; icon: LucideIcon; c: ComponentHealth }) {
  const tone = STATUS_TONE[c.status] ?? 'text-navy-300 border-border'
  return (
    <div className="card p-5">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-teal-400" />
          <span className="text-sm font-semibold text-navy-100">{title}</span>
        </div>
        <span className={`rounded-pill border px-2 py-0.5 text-[10px] font-semibold uppercase ${tone}`}>
          {c.status}
        </span>
      </div>
      {c.latency_ms != null && <p className="text-xs text-navy-400">Задержка: {c.latency_ms} мс</p>}
      {c.detail && <p className="text-xs text-risk-high">{c.detail}</p>}
      {c.meta && Object.keys(c.meta).length > 0 && (
        <dl className="mt-2 space-y-1">
          {Object.entries(c.meta).map(([k, v]) => (
            <div key={k} className="flex justify-between text-[11px]">
              <dt className="text-navy-500">{k}</dt>
              <dd className="font-mono text-navy-300">{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  )
}

export function AIMonitoring() {
  const { data, isFetching, refetch } = useQuery({
    queryKey: ['sys-health'],
    queryFn: fetchSystemHealth,
    refetchInterval: 15000,
  })

  if (!data) return <LoadingSpinner label="Проверка состояния систем…" />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-navy-50">AI-мониторинг платформы</h1>
          <p className="text-xs text-navy-400">
            Проверено {new Date(data.checked_at).toLocaleString('ru-RU')}
          </p>
        </div>
        <button onClick={() => refetch()} className="btn-ghost !px-3 !py-2" title="Обновить">
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <HealthCard title="Локальный LLM" icon={Cpu} c={data.llm} />
        <HealthCard title="Эмбеддинги" icon={Layers} c={data.embedding} />
        <HealthCard title="Reranker" icon={Boxes} c={data.reranker} />
        <HealthCard title="Redis" icon={Radio} c={data.redis} />
        <HealthCard title="Очередь воркеров" icon={Server} c={data.worker_queue} />
        <HealthCard title="PostgreSQL" icon={Database} c={data.postgres} />
        <HealthCard title="Vector DB (pgvector)" icon={Database} c={data.vector_db} />
      </div>
    </div>
  )
}

import { api } from './client'

export interface ComponentHealth {
  status: string
  detail?: string | null
  latency_ms?: number | null
  meta?: Record<string, unknown>
}

export interface SystemHealth {
  checked_at: string
  llm: ComponentHealth
  embedding: ComponentHealth
  reranker: ComponentHealth
  redis: ComponentHealth
  worker_queue: ComponentHealth
  postgres: ComponentHealth
  vector_db: ComponentHealth
}

export async function fetchSystemHealth(): Promise<SystemHealth> {
  const { data } = await api.get('/monitoring/health')
  return data
}

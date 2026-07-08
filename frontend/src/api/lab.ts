import { api } from './client'

export interface LabEvent {
  agent: string
  status: 'running' | 'done' | 'error' | 'finished'
  payload: Record<string, any>
  ts: string
}

export async function startLabAnalysis(payload: {
  text: string
  region: string
  category: string
}): Promise<{ task_id: string }> {
  const { data } = await api.post('/lab/analyze', payload)
  return data
}

/** Подписка на SSE-поток прогресса агентов. Возвращает функцию отписки. */
export function subscribeLabStream(
  taskId: string,
  onEvent: (event: LabEvent) => void,
  onClose: () => void,
): () => void {
  const source = new EventSource(`/api/lab/stream/${taskId}`, { withCredentials: true })
  source.addEventListener('progress', (e) => {
    const event: LabEvent = JSON.parse((e as MessageEvent).data)
    onEvent(event)
    if (event.agent === 'orchestrator' && (event.status === 'finished' || event.status === 'error')) {
      source.close()
      onClose()
    }
  })
  source.onerror = () => {
    source.close()
    onClose()
  }
  return () => source.close()
}

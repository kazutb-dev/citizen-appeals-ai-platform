import { AnimatePresence } from 'framer-motion'
import type { LabEvent } from '../../api/lab'
import { AGENTS } from './agentMeta'
import { AgentProgress } from './AgentProgress'
import type { AgentRunStatus } from './AgentProgress'
import { AgentResult } from './AgentResult'

export interface AgentState {
  status: AgentRunStatus
  payload: Record<string, any>
}

export function reduceLabEvents(events: LabEvent[]): Record<string, AgentState> {
  const state: Record<string, AgentState> = {}
  for (const e of events) {
    if (e.agent === 'orchestrator') continue
    state[e.agent] = {
      status: e.status === 'running' ? 'running' : e.status === 'done' ? 'done' : 'error',
      payload: e.payload ?? {},
    }
  }
  return state
}

function summarize(agent: string, s: AgentState): string | undefined {
  if (s.status !== 'done') return undefined
  const p = s.payload
  switch (agent) {
    case 'agent1':
      return p.risk_level ? `Риск: ${p.risk_level}` : undefined
    case 'agent2':
      return p.is_campaign ? 'Скоординированная группа выявлена' : 'Скоординированных групп не выявлено'
    case 'agent3':
      return p.is_duplicate ? `Дубликат #${p.duplicate_of_id}` : 'Дубликат не найден'
    case 'agent4':
      return p.confidence !== undefined ? 'Проект ответа готов' : undefined
    case 'agent5':
      return p.category ? `Профиль: ${p.category}` : undefined
    case 'agent6':
      return p.flagged ? 'Проблема лекобеспечения → аптека' : 'Признаков не выявлено'
    case 'agent7':
      return p.flagged ? 'Жалоба на качество → служба качества' : 'Признаков не выявлено'
    case 'agent8':
      return p.flagged ? `Санэпид-риск: ${p.severity ?? 'выявлен'}` : 'Санитарных рисков нет'
    default:
      return undefined
  }
}

export function AgentPanel({ state }: { state: Record<string, AgentState> }) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        {AGENTS.map((a) => (
          <AgentProgress
            key={a.key}
            agentKey={a.key}
            status={state[a.key]?.status ?? 'idle'}
            summary={state[a.key] ? summarize(a.key, state[a.key]) : undefined}
          />
        ))}
      </div>

      <AnimatePresence>
        {AGENTS.filter((a) => state[a.key]?.status === 'done' && a.key !== 'embedding').map((a) => (
          <AgentResult key={a.key} agentKey={a.key} payload={state[a.key].payload} />
        ))}
      </AnimatePresence>
    </div>
  )
}

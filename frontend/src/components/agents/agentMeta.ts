import {
  AlertTriangle,
  Copy,
  FileText,
  Network,
  Sparkles,
  UserSearch,
  Pill,
  Stethoscope,
  Biohazard,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface AgentMeta {
  key: string
  name: string
  short: string
  icon: LucideIcon
  color: string
}

export const AGENTS: AgentMeta[] = [
  { key: 'embedding', name: 'Векторизация текста', short: 'Embeddings', icon: Sparkles, color: 'text-accent' },
  { key: 'agent3', name: 'Агент 3: Дубликаты', short: 'Дубликаты', icon: Copy, color: 'text-amber-400' },
  { key: 'agent1', name: 'Агент 1: Эскалация руководству', short: 'Эскалация', icon: AlertTriangle, color: 'text-risk-critical' },
  { key: 'agent5', name: 'Агент 5: Повторные обращения', short: 'Повторные', icon: UserSearch, color: 'text-navy-200' },
  { key: 'agent2', name: 'Агент 2: Группировка обращений', short: "Группы", icon: Network, color: 'text-risk-high' },
  { key: 'agent4', name: 'Агент 4: Проект ответа', short: 'Ответ', icon: FileText, color: 'text-teal-400' },
  { key: 'agent6', name: 'Агент 6: Лекарственное обеспечение', short: 'Лекарства', icon: Pill, color: 'text-gold' },
  { key: 'agent7', name: 'Агент 7: Качество медпомощи', short: 'Качество', icon: Stethoscope, color: 'text-teal-300' },
  { key: 'agent8', name: 'Агент 8: Санэпид-контроль', short: 'Санэпид', icon: Biohazard, color: 'text-navy-200' },
]

export const AGENT_BY_KEY: Record<string, AgentMeta> = Object.fromEntries(
  AGENTS.map((a) => [a.key, a]),
)

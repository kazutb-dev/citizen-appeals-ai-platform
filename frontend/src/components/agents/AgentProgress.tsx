import { motion } from 'framer-motion'
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react'
import { AGENT_BY_KEY } from './agentMeta'

export type AgentRunStatus = 'idle' | 'running' | 'done' | 'error'

export function AgentProgress({
  agentKey,
  status,
  summary,
}: {
  agentKey: string
  status: AgentRunStatus
  summary?: string
}) {
  const meta = AGENT_BY_KEY[agentKey]
  if (!meta) return null

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-3 rounded-lg border border-border bg-surface px-4 py-3"
    >
      {status === 'running' && <Loader2 className="h-4 w-4 animate-spin text-teal-400" />}
      {status === 'done' && <CheckCircle2 className="h-4 w-4 text-risk-low" />}
      {status === 'error' && <XCircle className="h-4 w-4 text-risk-critical" />}
      {status === 'idle' && <Circle className="h-4 w-4 text-navy-500" />}

      <div className="flex-1">
        <p className="text-sm font-medium text-navy-100">{meta.name}</p>
        {summary && <p className="text-xs text-navy-300">{summary}</p>}
        {status === 'running' && (
          <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-border">
            <motion.div
              className="h-full bg-gradient-to-r from-primary to-accent"
              initial={{ x: '-100%' }}
              animate={{ x: '100%' }}
              transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut' }}
              style={{ width: '50%' }}
            />
          </div>
        )}
      </div>
    </motion.div>
  )
}

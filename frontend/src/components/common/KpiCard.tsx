import { motion } from 'framer-motion'
import { TrendingDown, TrendingUp } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface KpiCardProps {
  label: string
  value: string | number
  icon: LucideIcon
  trendPct?: number
  tone?: 'default' | 'critical' | 'warning' | 'success'
  sub?: string
  delay?: number
}

const TONES = {
  default:  { border: 'border-border',              icon: 'text-teal-400' },
  critical: { border: 'border-risk-critical/40',    icon: 'text-risk-critical' },
  warning:  { border: 'border-risk-medium/40',      icon: 'text-risk-medium' },
  success:  { border: 'border-risk-low/40',         icon: 'text-risk-low' },
}

export function KpiCard({ label, value, icon: Icon, trendPct, tone = 'default', sub, delay = 0 }: KpiCardProps) {
  const t = TONES[tone]
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: [0.16, 1, 0.3, 1] }}
      className={`card flex flex-col gap-2 p-5 ${t.border}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-navy-400">{label}</span>
        <Icon className={`h-4 w-4 ${t.icon}`} />
      </div>
      <div className="flex items-end gap-3">
        <span className="font-mono text-3xl font-semibold text-navy-50">{value}</span>
        {trendPct !== undefined && (
          <span
            className={`mb-1 flex items-center gap-1 text-xs font-medium ${
              trendPct >= 0 ? 'text-risk-high' : 'text-risk-low'
            }`}
          >
            {trendPct >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {Math.abs(trendPct).toFixed(0)}%
          </span>
        )}
      </div>
      {sub && <span className="text-[11px] text-navy-400">{sub}</span>}
    </motion.div>
  )
}

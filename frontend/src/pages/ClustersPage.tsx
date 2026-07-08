import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { TrendingUp } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchClusters } from '../api/clusters'
import { EmptyState } from '../components/common/EmptyState'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { CLUSTER_STATUS_LABELS, CLUSTER_TYPE_LABELS } from '../types/cluster'
import type { Cluster } from '../types/cluster'

function Meter({ label, value, danger }: { label: string; value: number; danger?: boolean }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-32 shrink-0 text-navy-400">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-border">
        <div
          className={`h-full rounded-full ${danger ? 'bg-gradient-to-r from-risk-high to-risk-critical' : 'bg-gradient-to-r from-primary to-accent'}`}
          style={{ width: `${Math.min(100, value * 100)}%` }}
        />
      </div>
      <span className="w-9 text-right font-mono text-navy-200">{Math.round(value * 100)}%</span>
    </div>
  )
}

function ClusterCard({ cluster, index }: { cluster: Cluster; index: number }) {
  const isCampaign = cluster.status === 'confirmed_campaign'
  const regions = Object.entries(cluster.region_spread)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`card p-5 ${isCampaign ? 'border-risk-critical/40' : ''}`}
    >
      <div className="mb-2 flex items-center justify-between">
        <span className={`text-xs font-bold uppercase tracking-wide ${isCampaign ? 'text-risk-critical' : 'text-teal-400'}`}>
          {isCampaign ? '🔴 Подтверждённая группа' : CLUSTER_STATUS_LABELS[cluster.status]}
        </span>
        <span className="rounded bg-surface-card px-2 py-0.5 text-[10px] text-navy-300">
          {CLUSTER_TYPE_LABELS[cluster.cluster_type]}
        </span>
      </div>

      <h3 className="mb-1 text-sm font-semibold text-navy-50">{cluster.name}</h3>
      <p className="mb-3 text-xs text-navy-400">
        {cluster.appeal_count} обращений · {cluster.requester_count} обращавшихся
      </p>

      {regions.length > 0 && (
        <p className="mb-3 text-xs text-navy-300">
          Локации: {regions.map(([r, n]) => `${r} (${n})`).join(', ')}
          {Object.keys(cluster.region_spread).length > 3 && '…'}
        </p>
      )}

      <div className="mb-3 space-y-1.5">
        <Meter label="Координация" value={cluster.coordination_score} danger={cluster.coordination_score > 0.65} />
        <Meter label="Сходство текстов" value={cluster.similarity_score} />
      </div>

      {cluster.peak_rate_per_hour > 0 && (
        <p className="mb-3 flex items-center gap-1.5 text-xs text-navy-300">
          <TrendingUp className="h-3.5 w-3.5 text-teal-400" />
          Пик: {Math.round(cluster.peak_rate_per_hour)} обращений/час
        </p>
      )}

      <Link to={`/clusters/${cluster.id}`} className="btn-ghost w-full justify-center !py-2 text-xs">
        Просмотреть обращения
      </Link>
    </motion.div>
  )
}

export function ClustersPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const { data: clusters, isLoading } = useQuery({
    queryKey: ['clusters', statusFilter],
    queryFn: () => fetchClusters(statusFilter ? { status: statusFilter } : {}),
  })

  return (
    <div className="space-y-4">
      <div className="card flex items-center gap-3 p-4">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input">
          <option value="">Все статусы</option>
          {Object.entries(CLUSTER_STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <p className="text-xs text-navy-400">
          Кластеры формируются Агентом 2 на основе семантического сходства обращений (pgvector).
        </p>
      </div>

      {isLoading ? (
        <LoadingSpinner label="Загрузка групп…" />
      ) : clusters?.length ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {clusters.map((c, i) => (
            <ClusterCard key={c.id} cluster={c} index={i} />
          ))}
        </div>
      ) : (
        <EmptyState title="Кластеры не обнаружены" />
      )}
    </div>
  )
}

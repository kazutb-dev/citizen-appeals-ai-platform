import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { fetchCluster, fetchClusterAppeals } from '../api/clusters'
import { AppealTable } from '../components/appeals/AppealTable'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { CLUSTER_STATUS_LABELS, CLUSTER_TYPE_LABELS } from '../types/cluster'

export function ClusterDetail() {
  const { id } = useParams()
  const clusterId = Number(id)

  const { data: cluster } = useQuery({
    queryKey: ['cluster', clusterId],
    queryFn: () => fetchCluster(clusterId),
  })
  const { data: appeals, isLoading } = useQuery({
    queryKey: ['cluster-appeals', clusterId],
    queryFn: () => fetchClusterAppeals(clusterId),
  })

  if (!cluster) return <LoadingSpinner label="Загрузка группы…" />

  return (
    <div className="space-y-4">
      <Link to="/clusters" className="inline-flex items-center gap-2 text-sm text-navy-300 hover:text-navy-100">
        <ArrowLeft className="h-4 w-4" /> К группам
      </Link>

      <div className="card p-6">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span
            className={`text-xs font-bold uppercase ${
              cluster.status === 'confirmed_campaign' ? 'text-risk-critical' : 'text-teal-400'
            }`}
          >
            {CLUSTER_STATUS_LABELS[cluster.status]}
          </span>
          <span className="rounded bg-surface-card px-2 py-0.5 text-[10px] text-navy-300">
            {CLUSTER_TYPE_LABELS[cluster.cluster_type]}
          </span>
        </div>
        <h1 className="text-lg font-semibold text-navy-50">{cluster.name}</h1>
        {cluster.description && <p className="mt-2 max-w-3xl text-sm text-navy-300">{cluster.description}</p>}

        <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
          <Stat label="Обращений" value={cluster.appeal_count} />
          <Stat label="Заявителей" value={cluster.requester_count} />
          <Stat label="Координация" value={`${Math.round(cluster.coordination_score * 100)}%`} />
          <Stat label="Пик в час" value={Math.round(cluster.peak_rate_per_hour)} />
        </div>
      </div>

      <div className="card">
        <h2 className="border-b border-border px-4 py-3 text-sm font-semibold text-navy-100">
          Обращения группы
        </h2>
        {isLoading ? <LoadingSpinner /> : <AppealTable appeals={appeals ?? []} />}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg bg-surface p-3">
      <p className="text-[10px] uppercase tracking-wider text-navy-400">{label}</p>
      <p className="mt-1 font-mono text-xl font-semibold text-navy-50">{value}</p>
    </div>
  )
}

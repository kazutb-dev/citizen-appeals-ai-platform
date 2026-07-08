import { api } from './client'
import type {
  AgentStat,
  AuditEntry,
  CategoryStat,
  OverviewKpi,
  RegionStat,
  TrendPoint,
} from '../types/analytics'
import type { Paginated } from '../types/common'

export async function fetchOverview(): Promise<OverviewKpi> {
  const { data } = await api.get('/analytics/overview')
  return data
}

export async function fetchTrends(days = 30): Promise<TrendPoint[]> {
  const { data } = await api.get('/analytics/trends', { params: { days } })
  return data
}

export async function fetchRegions(): Promise<RegionStat[]> {
  const { data } = await api.get('/analytics/regions')
  return data
}

export async function fetchCategories(): Promise<CategoryStat[]> {
  const { data } = await api.get('/analytics/categories')
  return data
}

export async function fetchAgentStats(): Promise<AgentStat[]> {
  const { data } = await api.get('/analytics/agents')
  return data
}

export async function fetchAudit(params: {
  action?: string
  entity_type?: string
  page?: number
  page_size?: number
}): Promise<Paginated<AuditEntry>> {
  const { data } = await api.get('/audit', { params })
  return data
}

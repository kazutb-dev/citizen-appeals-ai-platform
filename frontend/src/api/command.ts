import { api } from './client'

export interface RegionHeat {
  region: string
  total: number
  critical: number
  lat: number | null
  lng: number | null
}

export interface HospitalRank {
  hospital_id: number
  name: string
  total: number
  critical: number
}

export interface CategoryCount {
  category: string
  label: string
  count: number
}

export interface SituationSnapshot {
  generated_at: string
  appeals_today: number
  appeals_today_trend_pct: number
  critical_open: number
  escalations: number
  sla_violations: number
  campaigns: number
  duplicates: number
  medicine_shortage: number
  emergency_incidents: number
  ai_runs_today: number
  region_heatmap: RegionHeat[]
  hospital_ranking: HospitalRank[]
  category_breakdown: CategoryCount[]
}

export interface ExecutiveBrief {
  generated_at: string
  ai_available: boolean
  summary: string | null
  stats: Record<string, number>
  top_categories: CategoryCount[]
  top_regions: RegionHeat[]
}

export interface RootCause {
  cause: string
  likelihood: number
  evidence: string
}

export interface RootCauseReport {
  category: string
  category_label: string
  sample_size: number
  summary: string
  root_causes: RootCause[]
  recommended_actions: string[]
  ai_available: boolean
}

export interface TimelineEvent {
  timestamp: string
  kind: string
  title: string
  appeal_id: number | null
  category: string | null
  status: string | null
  detail: string | null
}

export interface PatientTimeline {
  requester_id: number
  full_name: string
  total_appeals: number
  events: TimelineEvent[]
}

export async function fetchSituation(tenantId?: number): Promise<SituationSnapshot> {
  const { data } = await api.get('/command-center/situation', {
    params: tenantId ? { tenant_id: tenantId } : {},
  })
  return data
}

export async function fetchExecutiveBrief(tenantId?: number): Promise<ExecutiveBrief> {
  const { data } = await api.get('/command-center/executive-brief', {
    params: tenantId ? { tenant_id: tenantId } : {},
  })
  return data
}

export async function fetchRootCause(category: string): Promise<RootCauseReport> {
  const { data } = await api.get('/command-center/root-cause', { params: { category } })
  return data
}

export async function fetchPatientTimeline(requesterId: number): Promise<PatientTimeline> {
  const { data } = await api.get(`/command-center/patient-timeline/${requesterId}`)
  return data
}

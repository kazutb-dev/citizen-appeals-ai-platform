export interface RegionHeat {
  region: string
  total: number
  critical: number
  lat?: number | null
  lng?: number | null
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
  appeals_24h: number
  appeals_today_trend_pct: number
  critical_open: number
  escalations: number
  sla_violations: number
  campaigns: number
  duplicates: number
  duplicates_24h: number
  in_progress_now: number
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

export interface CriticalQueueItem {
  id: number
  submitted_at: string
  region: string
  category: string
  category_label: string
  status: string
  sla_deadline: string
  responsible: string
  priority: 'P0' | 'P1' | string
  department_id?: number | null
  is_escalated: boolean
}

export interface AppealMapPoint {
  id: number
  title: string
  region: string
  hospital_id?: number | null
  hospital_name?: string | null
  category: string
  category_label: string
  status: string
  risk_level: string
  submitted_at: string
  latitude: number
  longitude: number
  location_name?: string | null
}

export interface HotspotItem {
  name: string
  total: number
  critical: number
  overdue: number
  open_count: number
}

export interface HotspotsOut {
  generated_at: string
  regions: HotspotItem[]
  organizations: HotspotItem[]
}

export interface ActionItem {
  problem: string
  action: string
  assignee: string
}

export interface AiActionsOut {
  generated_at: string
  ai_available: boolean
  source: 'llm' | 'rules' | string
  items: ActionItem[]
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

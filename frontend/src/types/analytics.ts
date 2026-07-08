export interface OverviewKpi {
  appeals_today: number
  appeals_today_trend_pct: number
  critical_open: number
  campaigns_detected: number
  ai_processed: number
  ai_processed_pct: number
  avg_response_days: number
  total_appeals: number
}

export interface TrendPoint {
  date: string
  count: number
  critical: number
}

export interface RegionStat {
  region: string
  total: number
  critical: number
  escalated: number
  campaigns: number
}

export interface CategoryStat {
  category: string
  count: number
}

export interface AgentStat {
  agent: string
  name: string
  processed: number
  flagged: number
}

export interface AuditEntry {
  id: number
  user_id?: number | null
  actor: string
  action: string
  entity_type: string
  entity_id?: number | null
  details: Record<string, unknown>
  created_at: string
}

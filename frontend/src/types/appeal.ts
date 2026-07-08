import type { AppealStatus, RiskLevel } from './common'
import type { RequesterBrief } from './requester'

export interface AppealBrief {
  id: number
  title: string
  category: string
  subcategory?: string | null
  region: string
  status: AppealStatus
  risk_level: RiskLevel
  risk_score: number
  is_escalated: boolean
  is_campaign: boolean
  is_duplicate: boolean
  from_repeat_complainant: boolean
  submitted_at: string
  requester?: RequesterBrief | null
  source_channel?: string | null
  latitude?: number | null
  longitude?: number | null
  location_name?: string | null
}

export interface DraftBrief {
  id: number
  draft_text: string
  legal_references: { document?: string; law?: string; doc_type?: string; similarity?: number }[]
  confidence_score: number
  status: string
  generation_model?: string | null
  generation_time_ms?: number | null
  created_at: string
}

export interface Attachment {
  id: number
  filename: string
  content_type?: string | null
  size_bytes: number
  created_at: string
}

export interface AppealEvent {
  id: number
  event_type: string
  actor: string
  comment?: string | null
  details: Record<string, unknown>
  created_at: string
}

export interface AppealDetail extends AppealBrief {
  text: string
  district?: string | null
  external_id?: string | null
  department_id?: number | null
  risk_reasons: string[]
  escalation_level?: string | null
  escalation_reason?: string | null
  escalated_at?: string | null
  campaign_score: number
  campaign_cluster_id?: number | null
  duplicate_of_id?: number | null
  duplicate_score: number
  tags?: string[] | null
  analyzed_at?: string | null
  resolved_at?: string | null
  created_at: string
  draft_response?: DraftBrief | null
  attachments: Attachment[]
}

export interface MyAppealBrief {
  id: number
  title: string
  category: string
  subcategory?: string | null
  region: string
  status: AppealStatus
  submitted_at: string
  resolved_at?: string | null
}

export interface MyAppealDetail extends MyAppealBrief {
  text: string
  district?: string | null
  latitude?: number | null
  longitude?: number | null
  location_name?: string | null
  attachments: Attachment[]
  events: AppealEvent[]
  official_response?: string | null
  response_status?: string | null
  expected_response_time?: string | null
  responsible_department?: string | null
}

export interface AppealSubmit {
  title: string
  text: string
  category: string
  subcategory?: string | null
  region: string
  district?: string | null
  latitude: number
  longitude: number
  location_name?: string | null
}

export interface AppealFilters {
  status?: string
  region?: string
  category?: string
  risk_level?: string
  is_escalated?: boolean
  is_campaign?: boolean
  search?: string
  page?: number
  page_size?: number
}

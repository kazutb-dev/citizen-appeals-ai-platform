export interface RequesterBrief {
  id: number
  full_name: string
  requester_type: string
  affiliation?: string | null
  region?: string | null
  category: string
  is_repeat_complainant: boolean
}

export interface Requester extends RequesterBrief {
  total_appeals: number
  resolved_appeals: number
  rejected_appeals: number
  first_appeal_date?: string | null
  last_appeal_date?: string | null
  category_score: number
  repeat_score: number
  top_topics: string[]
  top_regions: string[]
  behavior_stats: { avg_per_month?: number; top_topic_share?: number }
  created_at: string
}

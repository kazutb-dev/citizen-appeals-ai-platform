export interface Cluster {
  id: number
  name: string
  description?: string | null
  cluster_type: 'coordinated_campaign' | 'duplicate' | 'campaign' | 'mass_complaint' | 'group_issue' | 'topic_group'
  topic: string
  category: string
  appeal_count: number
  requester_count: number
  region_spread: Record<string, number>
  growth_rate: number
  peak_rate_per_hour: number
  is_trending: boolean
  trend_score: number
  coordination_score: number
  similarity_score: number
  status: 'active' | 'monitoring' | 'resolved' | 'confirmed_campaign'
  first_seen?: string | null
  last_updated: string
}

export const CLUSTER_TYPE_LABELS: Record<string, string> = {
  coordinated_campaign: 'Координированная кампания',
  duplicate: 'Дубликаты',
  campaign: 'Скоординированная группа',
  mass_complaint: 'Массовая проблема',
  group_issue: 'Системная проблема',
  topic_group: 'Тематическая группа',
}

export const CLUSTER_STATUS_LABELS: Record<string, string> = {
  active: 'Активна',
  monitoring: 'Мониторинг',
  resolved: 'Закрыта',
  confirmed_campaign: 'Подтверждённая группа',
}

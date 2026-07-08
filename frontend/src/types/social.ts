export type Platform =
  | 'telegram'
  | 'tiktok'
  | 'instagram'
  | 'youtube'
  | 'facebook'
  | 'vk'
  | 'x'

export interface SocialPost {
  id: number
  platform: Platform
  source_id?: number | null
  source_account: string
  source_name: string
  post_url?: string | null
  post_text: string
  post_date: string
  views: number
  likes: number
  comments: number
  shares: number
  topic?: string | null
  category?: string | null
  region?: string | null
  risk_level: string
  sentiment: 'positive' | 'neutral' | 'negative' | 'alarming'
  tags?: string[] | null
  is_converted_to_appeal: boolean
  linked_appeal_id?: number | null
}

export interface TrendingTopic {
  topic: string
  category?: string | null
  post_count: number
  total_views: number
  max_risk_level: string
}

export interface SentimentPoint {
  date: string
  positive: number
  neutral: number
  negative: number
  alarming: number
}

export interface TopicTrend {
  topic: string
  current_count: number
  previous_count: number
  growth_pct: number
  dominant_sentiment: string
}

export interface SpikePoint {
  date: string
  count: number
  expected: number
  deviation: number
}

export interface SourceActivity {
  source_name: string
  platform: string
  post_count: number
  total_views: number
  negative_share: number
}

export interface ReputationPoint {
  date: string
  score: number
  post_count: number
}

export interface DepartmentImpact {
  category: string
  department?: string | null
  post_count: number
  negative_count: number
  total_views: number
}

export const PLATFORM_LABELS: Record<string, string> = {
  telegram: 'Telegram',
  tiktok: 'TikTok',
  instagram: 'Instagram',
  youtube: 'YouTube',
  facebook: 'Facebook',
  vk: 'ВКонтакте',
  x: 'X (Twitter)',
}

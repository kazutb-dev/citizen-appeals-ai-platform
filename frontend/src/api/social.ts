import { api } from './client'
import type { Paginated } from '../types/common'
import type {
  DepartmentImpact,
  ReputationPoint,
  SentimentPoint,
  SocialPost,
  SourceActivity,
  SpikePoint,
  TopicTrend,
  TrendingTopic,
} from '../types/social'

export async function fetchSocialPosts(params: {
  platform?: string
  category?: string
  region?: string
  risk_level?: string
  sentiment?: string
  page?: number
  page_size?: number
}): Promise<Paginated<SocialPost>> {
  const { data } = await api.get('/social/posts', { params })
  return data
}

export async function fetchTrending(): Promise<TrendingTopic[]> {
  const { data } = await api.get('/social/trending')
  return data
}

export async function fetchSentiment(days = 30): Promise<SentimentPoint[]> {
  const { data } = await api.get('/social/analytics/sentiment', { params: { days } })
  return data
}

export async function fetchTopicTrends(): Promise<TopicTrend[]> {
  const { data } = await api.get('/social/analytics/trends')
  return data
}

export async function fetchSpikes(): Promise<SpikePoint[]> {
  const { data } = await api.get('/social/analytics/spikes')
  return data
}

export async function fetchSourceActivity(): Promise<SourceActivity[]> {
  const { data } = await api.get('/social/analytics/sources')
  return data
}

export async function fetchReputation(days = 30): Promise<ReputationPoint[]> {
  const { data } = await api.get('/social/analytics/reputation', { params: { days } })
  return data
}

export async function fetchDepartmentImpact(): Promise<DepartmentImpact[]> {
  const { data } = await api.get('/social/analytics/department-impact')
  return data
}

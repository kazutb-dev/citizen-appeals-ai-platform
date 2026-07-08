import { api } from './client'

export interface RiskComponent {
  key: string
  label: string
  value: number
  contribution: number
}

export interface RiskScore {
  scope: string
  key: string
  label: string
  score: number
  level: 'low' | 'moderate' | 'elevated' | 'high' | 'critical'
  total_appeals: number
  growth_pct: number
  components: RiskComponent[]
  reasons: string[]
}

export interface RiskIndex {
  generated_at: string
  national: RiskScore
  regions: RiskScore[]
}

export interface ForecastPoint {
  day: string
  predicted: number
  lower: number
  upper: number
  is_forecast: boolean
}

export interface ForecastDriver {
  scope: 'region' | 'category'
  key: string
  label: string
  region: string | null
  expected_next: number
  change_pct: number
  confidence: number
  direction: 'up' | 'down' | 'stable'
}

export interface Forecast {
  generated_at: string
  horizon_days: number
  series: ForecastPoint[]
  expected_total: number
  expected_change_pct: number
  expected_critical: number
  confidence: number
  trend: 'up' | 'down' | 'stable'
  drivers: ForecastDriver[]
}

export interface WarningSignal {
  type: string
  title: string
  scope: string
  category: string | null
  severity: 'critical' | 'high' | 'medium' | 'low'
  confidence: number
  magnitude: number
  predicted_impact: string
  actions: string[]
}

export interface EarlyWarning {
  signals: WarningSignal[]
  counts: Record<string, number>
  total: number
}

export interface RegionRank {
  region: string
  score: number
  level: string
  total_appeals: number
  growth_pct: number
  resolution_rate: number
}

export interface RegionalComparison {
  generated_at: string
  ranking: RegionRank[]
  best: RegionRank[]
  worst: RegionRank[]
  improving: RegionRank[]
  deteriorating: RegionRank[]
}

export interface CopilotResult {
  region: string
  ai_available: boolean
  briefing: string | null
  risk: RiskScore | null
  forecast: { expected_total: number; expected_change_pct: number; confidence: number; trend: string }
  drivers: ForecastDriver[]
  warnings: WarningSignal[]
}

export async function fetchRiskIndex(): Promise<RiskIndex> {
  const { data } = await api.get('/intelligence/risk-index')
  return data
}

export async function fetchForecast(days = 7): Promise<Forecast> {
  const { data } = await api.get('/intelligence/forecast', { params: { days } })
  return data
}

export async function fetchEarlyWarning(): Promise<EarlyWarning> {
  const { data } = await api.get('/intelligence/early-warning')
  return data
}

export async function fetchRegionalComparison(): Promise<RegionalComparison> {
  const { data } = await api.get('/intelligence/regional-comparison')
  return data
}

export async function fetchCopilot(region?: string): Promise<CopilotResult> {
  const { data } = await api.get('/intelligence/copilot', { params: region ? { region } : {} })
  return data
}

import { api } from './client'
import type {
  AiActionsOut,
  AppealMapPoint,
  CategoryCount,
  CriticalQueueItem,
  ExecutiveBrief,
  HotspotsOut,
  PatientTimeline,
  RootCauseReport,
  SituationSnapshot,
} from '../types/situation'

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

export async function fetchCriticalQueue(tenantId?: number): Promise<CriticalQueueItem[]> {
  const { data } = await api.get('/command-center/critical-queue', {
    params: tenantId ? { tenant_id: tenantId } : {},
  })
  return data
}

export async function fetchAppealsMap(params: {
  tenant_id?: number
  period_hours?: number
  region?: string
  hospital_id?: number
  risk_level?: string
  status?: string
} = {}): Promise<AppealMapPoint[]> {
  const { data } = await api.get('/command-center/appeals-map', { params })
  return data
}

export async function fetchHotspots(params: {
  tenant_id?: number
  period_hours?: number
} = {}): Promise<HotspotsOut> {
  const { data } = await api.get('/command-center/hotspots', { params })
  return data
}

export async function fetchAiActions(params: {
  tenant_id?: number
  period_hours?: number
} = {}): Promise<AiActionsOut> {
  const { data } = await api.get('/command-center/ai-actions', { params })
  return data
}

export type { CategoryCount }

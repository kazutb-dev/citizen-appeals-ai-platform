import { api } from './client'
import type {
  AppealBrief,
  AppealDetail,
  AppealFilters,
  AppealSubmit,
  MyAppealBrief,
  MyAppealDetail,
} from '../types/appeal'
import type { Paginated } from '../types/common'

export async function fetchAppeals(filters: AppealFilters = {}): Promise<Paginated<AppealBrief>> {
  const { data } = await api.get('/appeals', { params: filters })
  return data
}

export async function fetchAppeal(id: number): Promise<AppealDetail> {
  const { data } = await api.get(`/appeals/${id}`)
  return data
}

export async function updateAppealStatus(
  id: number,
  status: string,
  comment?: string,
): Promise<AppealDetail> {
  const { data } = await api.put(`/appeals/${id}/status`, { status, comment })
  return data
}

export async function reanalyzeAppeal(id: number): Promise<{ detail: string }> {
  const { data } = await api.post(`/appeals/${id}/analyze`)
  return data
}

export async function escalateAppeal(id: number): Promise<AppealDetail> {
  const { data } = await api.post(`/appeals/${id}/escalate`)
  return data
}

export async function createAppeal(payload: {
  title: string
  text: string
  category: string
  subcategory?: string
  region: string
  requester_full_name: string
  requester_identifier: string
  requester_type?: string
  affiliation?: string
}): Promise<AppealDetail> {
  const { data } = await api.post('/appeals', payload)
  return data
}

// === Портал заявителя ===

export async function submitAppeal(payload: AppealSubmit): Promise<MyAppealDetail> {
  const { data } = await api.post('/appeals/submit', payload)
  return data
}

export async function fetchMyAppeals(params: {
  status?: string
  page?: number
  page_size?: number
} = {}): Promise<Paginated<MyAppealBrief>> {
  const { data } = await api.get('/appeals/my', { params })
  return data
}

export async function fetchMyAppeal(id: number): Promise<MyAppealDetail> {
  const { data } = await api.get(`/appeals/my/${id}`)
  return data
}

export async function uploadAttachment(appealId: number, file: File): Promise<AppealDetail> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post(`/appeals/${appealId}/attachments`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export function attachmentUrl(appealId: number, attachmentId: number): string {
  return `/api/appeals/${appealId}/attachments/${attachmentId}`
}

/** Результаты запуска агентов 1–8 из журнала аудита для данного обращения. */
export async function fetchAppealAnalysis(id: number): Promise<Record<string, Record<string, any>>> {
  const { data } = await api.get(`/appeals/${id}/analysis`)
  return data
}

import { api } from './client'
import type { AppealBrief, DraftBrief } from '../types/appeal'
import type { Paginated } from '../types/common'

export interface Draft extends DraftBrief {
  appeal_id: number
  reviewed_by_id?: number | null
  reviewed_at?: string | null
  appeal?: AppealBrief | null
}

export async function fetchDrafts(params: {
  status?: string
  page?: number
  page_size?: number
}): Promise<Paginated<Draft>> {
  const { data } = await api.get('/drafts', { params })
  return data
}

export async function fetchDraft(id: number): Promise<Draft> {
  const { data } = await api.get(`/drafts/${id}`)
  return data
}

export async function updateDraft(id: number, draft_text: string): Promise<Draft> {
  const { data } = await api.put(`/drafts/${id}`, { draft_text })
  return data
}

export async function approveDraft(id: number): Promise<Draft> {
  const { data } = await api.post(`/drafts/${id}/approve`)
  return data
}

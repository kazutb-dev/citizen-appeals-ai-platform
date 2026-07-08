import { api } from './client'
import type { AppealBrief } from '../types/appeal'
import type { Paginated } from '../types/common'
import type { Requester } from '../types/requester'

export async function fetchRequesters(params: {
  category?: string
  requester_type?: string
  region?: string
  search?: string
  page?: number
  page_size?: number
}): Promise<Paginated<Requester>> {
  const { data } = await api.get('/requesters', { params })
  return data
}

export async function fetchRequester(id: number): Promise<Requester> {
  const { data } = await api.get(`/requesters/${id}`)
  return data
}

export async function fetchRequesterAppeals(id: number): Promise<AppealBrief[]> {
  const { data } = await api.get(`/requesters/${id}/appeals`)
  return data
}

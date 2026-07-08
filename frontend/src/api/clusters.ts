import { api } from './client'
import type { AppealBrief } from '../types/appeal'
import type { Cluster } from '../types/cluster'

export async function fetchClusters(params: {
  status?: string
  cluster_type?: string
} = {}): Promise<Cluster[]> {
  const { data } = await api.get('/clusters', { params })
  return data
}

export async function fetchCluster(id: number): Promise<Cluster> {
  const { data } = await api.get(`/clusters/${id}`)
  return data
}

export async function fetchClusterAppeals(id: number): Promise<AppealBrief[]> {
  const { data } = await api.get(`/clusters/${id}/appeals`)
  return data
}

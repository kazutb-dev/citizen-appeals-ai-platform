import { api } from './client'

export interface IntegrationProvider {
  key: string
  name: string
  kind: string
  direction: string
  description: string
  capabilities: string[]
  mode: string
  status: string
}

export interface IntegrationMessage {
  external_id: string
  channel: string
  author: string
  text: string
  received_at: string
  category_hint: string | null
  meta: Record<string, unknown>
}

export async function fetchIntegrationCatalog(): Promise<IntegrationProvider[]> {
  const { data } = await api.get('/integration-center/catalog')
  return data
}

export async function testIntegration(
  key: string,
): Promise<{ ok: boolean; mode: string; message: string }> {
  const { data } = await api.post(`/integration-center/${key}/test`)
  return data
}

export async function fetchIntegrationSample(
  key: string,
  limit = 5,
): Promise<IntegrationMessage[]> {
  const { data } = await api.get(`/integration-center/${key}/sample`, { params: { limit } })
  return data
}

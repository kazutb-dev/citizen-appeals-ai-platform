import { api } from './client'
import type {
  AgentSetting,
  Department,
  Integration,
  KnowledgeDocument,
  SocialSource,
  SocialSourceInput,
} from '../types/admin'
import type { User } from '../types/common'

// === AI-агенты ===

export async function fetchAgentSettings(): Promise<AgentSetting[]> {
  const { data } = await api.get('/admin/agents')
  return data
}

export async function updateAgentSetting(
  agentKey: string,
  payload: {
    is_enabled?: boolean
    config?: Record<string, unknown>
    prompt_template?: string
  },
): Promise<AgentSetting> {
  const { data } = await api.put(`/admin/agents/${agentKey}`, payload)
  return data
}

// === Социальные источники ===

export async function fetchSocialSources(): Promise<SocialSource[]> {
  const { data } = await api.get('/admin/social-sources')
  return data
}

export async function createSocialSource(payload: SocialSourceInput): Promise<SocialSource> {
  const { data } = await api.post('/admin/social-sources', payload)
  return data
}

export async function updateSocialSource(
  id: number,
  payload: Partial<SocialSourceInput>,
): Promise<SocialSource> {
  const { data } = await api.put(`/admin/social-sources/${id}`, payload)
  return data
}

export async function deleteSocialSource(id: number): Promise<{ detail: string }> {
  const { data } = await api.delete(`/admin/social-sources/${id}`)
  return data
}

export async function pollSocialSource(id: number): Promise<{ detail: string }> {
  const { data } = await api.post(`/admin/social-sources/${id}/poll`)
  return data
}

// === Интеграции ===

export async function fetchIntegrations(): Promise<Integration[]> {
  const { data } = await api.get('/admin/integrations')
  return data
}

export async function updateInstagram(payload: {
  app_id?: string
  business_account_id?: string
  app_secret?: string
  access_token?: string
  refresh_token?: string
}): Promise<Integration> {
  const { data } = await api.put('/admin/integrations/instagram', payload)
  return data
}

export async function instagramOauthUrl(): Promise<{ oauth_url: string; redirect_uri: string }> {
  const { data } = await api.get('/admin/integrations/instagram/oauth-url')
  return data
}

export async function instagramOauthExchange(code: string, state: string): Promise<Integration> {
  const { data } = await api.post('/admin/integrations/instagram/oauth/exchange', { code, state })
  return data
}

export async function instagramHealthCheck(): Promise<Integration> {
  const { data } = await api.post('/admin/integrations/instagram/health')
  return data
}

// === База знаний ===

export async function fetchKnowledge(): Promise<KnowledgeDocument[]> {
  const { data } = await api.get('/admin/knowledge')
  return data
}

export async function uploadKnowledge(
  file: File,
  params: { title: string; doc_type: string; department_id?: number },
): Promise<KnowledgeDocument> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/admin/knowledge/upload', form, {
    params,
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function reprocessKnowledge(id: number): Promise<KnowledgeDocument> {
  const { data } = await api.post(`/admin/knowledge/${id}/reprocess`)
  return data
}

export async function deleteKnowledge(id: number): Promise<{ detail: string }> {
  const { data } = await api.delete(`/admin/knowledge/${id}`)
  return data
}

// === Пользователи ===

export async function fetchUsers(role?: string): Promise<User[]> {
  const { data } = await api.get('/admin/users', { params: role ? { role } : {} })
  return data
}

export async function updateUser(
  id: number,
  payload: { role?: string; is_active?: boolean; department_id?: number; position?: string },
): Promise<User> {
  const { data } = await api.put(`/admin/users/${id}`, payload)
  return data
}

// === Подразделения ===

export async function fetchDepartments(): Promise<Department[]> {
  const { data } = await api.get('/admin/departments')
  return data
}

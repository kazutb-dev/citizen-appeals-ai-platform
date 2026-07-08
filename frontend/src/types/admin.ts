export interface AgentSetting {
  id: number
  agent_key: string
  display_name: string
  description?: string | null
  is_enabled: boolean
  config: Record<string, unknown>
  prompt_template?: string | null
  updated_at: string
}

export interface SocialSource {
  id: number
  name: string
  platform: string
  url?: string | null
  has_credentials: boolean
  polling_interval_minutes: number
  is_enabled: boolean
  last_polled_at?: string | null
  last_status: string
  last_error?: string | null
  created_at: string
}

export interface SocialSourceInput {
  name: string
  platform: string
  url?: string | null
  credentials?: Record<string, string>
  polling_interval_minutes?: number
  is_enabled?: boolean
}

export interface Integration {
  provider: string
  config: Record<string, string>
  secrets_masked: Record<string, string>
  status: string
  token_expires_at?: string | null
  last_health_check_at?: string | null
  last_health_status?: string | null
}

export interface KnowledgeDocument {
  id: number
  title: string
  doc_type: string
  department_id?: number | null
  filename?: string | null
  status: string
  error?: string | null
  chunk_count: number
  created_at: string
}

export interface Department {
  id: number
  name: string
  short_name?: string | null
  code?: string | null
  department_type: string
  categories?: string[] | null
  contact_email?: string | null
}

export const DOC_TYPE_LABELS: Record<string, string> = {
  regulation: 'Положение',
  policy: 'Политика',
  academic_rule: 'Клинический протокол',
  handbook: 'Справочник пациента',
  hr_policy: 'HR-политика',
  procedure: 'Процедура',
}

export const SOURCE_STATUS_LABELS: Record<string, string> = {
  pending: 'Ожидает первого опроса',
  ok: 'Работает',
  error: 'Ошибка',
  not_configured: 'Не настроен',
}

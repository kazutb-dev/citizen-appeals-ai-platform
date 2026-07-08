import { enUS, kk, ru } from 'date-fns/locale'
import type { Locale } from 'date-fns'
import { useTranslation } from 'react-i18next'

/** Ключи доменных перечислений — единый источник для селектов и переводов. */
export const CATEGORY_KEYS = [
  'medicines', 'emergency', 'hospitalization', 'quality_of_care', 'access',
  'medical_staff', 'diagnostics', 'preventive', 'financial', 'sanitary',
  'documents', 'legal', 'other',
] as const

export const STATUS_KEYS = [
  'new', 'analyzing', 'pending_review', 'in_progress', 'escalated',
  'resolved', 'rejected', 'duplicate',
] as const

export const RISK_KEYS = ['critical', 'high', 'medium', 'low'] as const

export const REQUESTER_TYPE_KEYS = [
  'patient', 'relative', 'medical_worker', 'guardian', 'external',
] as const

/**
 * Хук доменных подписей. Использует i18next через useTranslation, поэтому
 * компоненты автоматически перерисовываются при смене языка. Возвращает
 * функции key -> локализованная подпись (с откатом на сам ключ).
 */
export function useLabels() {
  const { t } = useTranslation()
  const make = (ns: string) => (key?: string | null): string =>
    key ? t(`${ns}.${key}`, { defaultValue: key }) : ''
  return {
    category: make('categories'),
    status: make('status'),
    risk: make('risk'),
    requesterType: make('requesterType'),
    requesterCategory: make('requesterCategory'),
    escalation: make('escalation'),
    clusterStatus: make('clusterStatus'),
    role: make('roles'),
  }
}

/** Локализованные опции категорий для выпадающих списков. */
export function useCategoryOptions() {
  const { t } = useTranslation()
  return CATEGORY_KEYS.map((value) => ({
    value,
    label: t(`categories.${value}`, { defaultValue: value }),
  }))
}

/** Локаль date-fns для форматирования дат в соответствии с выбранным языком. */
export function useDateFnsLocale(): Locale {
  const { i18n } = useTranslation()
  const lng = i18n.resolvedLanguage
  return lng === 'kk' ? kk : lng === 'en' ? enUS : ru
}

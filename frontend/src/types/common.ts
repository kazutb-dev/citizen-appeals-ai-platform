export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export type RiskLevel = 'critical' | 'high' | 'medium' | 'low'

export type AppealStatus =
  | 'new'
  | 'analyzing'
  | 'pending_review'
  | 'in_progress'
  | 'escalated'
  | 'resolved'
  | 'rejected'
  | 'duplicate'

export type UserRole = 'admin' | 'analyst' | 'operator' | 'viewer' | 'requester'

export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  position?: string | null
  department_id?: number | null
  requester_id?: number | null
  is_active: boolean
  last_login_at?: string | null
}

export const CATEGORY_LABELS: Record<string, string> = {
  medicines: 'Лекарственное обеспечение',
  emergency: 'Скорая и неотложная помощь',
  hospitalization: 'Госпитализация и стационар',
  quality_of_care: 'Качество медицинской помощи',
  access: 'Доступность и запись к врачу',
  medical_staff: 'Работа медицинского персонала',
  diagnostics: 'Диагностика и обследования',
  preventive: 'Профилактика и вакцинация',
  financial: 'ОСМС и платные услуги',
  sanitary: 'Санитария и инфекционная безопасность',
  documents: 'Медицинские документы и справки',
  legal: 'Права пациентов',
  other: 'Прочее',
}

export const SUBCATEGORY_LABELS: Record<string, string> = {
  // Лекарственное обеспечение
  drug_shortage: 'Отсутствие лекарств',
  free_drugs: 'Льготные и бесплатные лекарства',
  pharmacy: 'Работа аптеки',
  prescription: 'Выписка рецепта',
  drug_quality: 'Качество препаратов',
  // Скорая и неотложная помощь
  ambulance_delay: 'Задержка скорой помощи',
  ambulance_refusal: 'Отказ в выезде',
  emergency_care: 'Экстренная помощь',
  triage: 'Сортировка в приёмном отделении',
  // Госпитализация и стационар
  admission_refusal: 'Отказ в госпитализации',
  discharge: 'Выписка из стационара',
  ward_conditions: 'Условия пребывания в палате',
  nutrition: 'Питание в стационаре',
  bed_shortage: 'Отсутствие мест',
  // Качество медицинской помощи
  misdiagnosis: 'Ошибка диагностики',
  treatment_quality: 'Качество лечения',
  malpractice: 'Врачебная ошибка / халатность',
  complications: 'Осложнения после лечения',
  care_refusal: 'Отказ в оказании помощи',
  // Доступность и запись
  appointment: 'Запись на приём',
  queue: 'Очереди и ожидание',
  attachment: 'Прикрепление к поликлинике',
  referral: 'Направление к специалисту',
  remote_area: 'Доступность в сельской местности',
  // Медицинский персонал
  ethics: 'Этика и деонтология',
  rudeness: 'Грубость персонала',
  competence: 'Компетентность врача',
  staff_shortage: 'Нехватка специалистов',
  // Диагностика
  lab_tests: 'Лабораторные анализы',
  imaging: 'КТ / МРТ / УЗИ / рентген',
  results_delay: 'Задержка результатов',
  equipment: 'Медицинское оборудование',
  // Профилактика
  vaccination: 'Вакцинация',
  screening: 'Скрининг и диспансеризация',
  maternal: 'Охрана материнства и детства',
  health_promotion: 'Санитарное просвещение',
  // ОСМС и платные услуги
  osms: 'ОСМС (медстрахование)',
  paid_services: 'Платные услуги',
  illegal_payment: 'Неформальные платежи / поборы',
  reimbursement: 'Возмещение расходов',
  // Санитария
  infection_outbreak: 'Вспышка инфекции',
  sanitary_conditions: 'Санитарное состояние',
  sterility: 'Стерильность и дезинфекция',
  waste: 'Медицинские отходы',
  // Документы
  medical_certificate: 'Медицинская справка',
  sick_leave: 'Больничный лист',
  medical_record: 'Медицинская карта / выписка',
  disability: 'Оформление инвалидности',
  // Права пациентов
  complaint: 'Жалоба',
  patient_rights: 'Нарушение прав пациента',
  consent: 'Информированное согласие',
  data_privacy: 'Врачебная тайна и данные',
}

export const STATUS_LABELS: Record<string, string> = {
  new: 'Новое',
  analyzing: 'Анализ ИИ',
  pending_review: 'Ожидает проверки',
  in_progress: 'В работе',
  escalated: 'Эскалировано',
  resolved: 'Решено',
  rejected: 'Отклонено',
  duplicate: 'Дубликат',
}

export const RISK_LABELS: Record<RiskLevel, string> = {
  critical: 'Критический',
  high: 'Высокий',
  medium: 'Средний',
  low: 'Низкий',
}

export const REQUESTER_TYPE_LABELS: Record<string, string> = {
  patient: 'Пациент',
  relative: 'Родственник пациента',
  medical_worker: 'Медицинский работник',
  guardian: 'Законный представитель',
  external: 'Внешний заявитель',
}

// Поведенческие категории заявителя (Агент 5)
export const REQUESTER_CATEGORY_LABELS: Record<string, string> = {
  active_citizen: 'Активный заявитель',
  digital_activist: 'Цифровой активист',
  chronic_complainant: 'Хронический заявитель',
  coordinator: 'Координатор',
  emotional_crisis: 'Эмоционально-кризисное состояние',
  expert_observer: 'Эксперт-наблюдатель',
}

export const ESCALATION_LABELS: Record<string, string> = {
  chief_doctor: 'Главный врач',
  deputy_chief: 'Заместитель главного врача',
  head_of_department: 'Заведующий отделением',
}

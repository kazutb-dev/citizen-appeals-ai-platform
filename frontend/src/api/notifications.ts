import { api } from './client'
import type { Notification, PaginatedNotifications } from '../types/notification'

export async function fetchNotifications(params: {
  unread_only?: boolean
  page?: number
  page_size?: number
} = {}): Promise<PaginatedNotifications> {
  const { data } = await api.get('/notifications', { params })
  return data
}

export async function markNotificationRead(id: number): Promise<Notification> {
  const { data } = await api.post(`/notifications/${id}/read`)
  return data
}

export async function markAllNotificationsRead(): Promise<{ detail: string }> {
  const { data } = await api.post('/notifications/read-all')
  return data
}

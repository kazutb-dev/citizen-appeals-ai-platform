export interface Notification {
  id: number
  appeal_id?: number | null
  type: string
  title: string
  body?: string | null
  is_read: boolean
  created_at: string
}

export interface PaginatedNotifications {
  items: Notification[]
  total: number
  unread: number
  page: number
  page_size: number
}

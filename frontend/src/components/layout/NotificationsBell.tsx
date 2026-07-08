import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Bell } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../../api/notifications'
import { useAuth } from '../../hooks/useAuth'

export function NotificationsBell() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const { data } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => fetchNotifications({ page_size: 10 }),
    refetchInterval: 60_000,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['notifications'] })
  const readMutation = useMutation({ mutationFn: markNotificationRead, onSuccess: invalidate })
  const readAllMutation = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidate })

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const openNotification = (id: number, appealId?: number | null) => {
    readMutation.mutate(id)
    setOpen(false)
    if (appealId) {
      navigate(user?.role === 'requester' ? `/appeal/${appealId}` : `/appeals/${appealId}`)
    }
  }

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} className="btn-ghost relative !px-3 !py-2" title="Уведомления">
        <Bell className="h-4 w-4" />
        {(data?.unread ?? 0) > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-risk-critical px-1 font-mono text-[9px] font-bold text-white">
            {data!.unread > 9 ? '9+' : data!.unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-11 z-50 w-80 rounded-xl border border-border bg-surface-card shadow-xl">
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <span className="text-xs font-semibold text-navy-200">Уведомления</span>
            {(data?.unread ?? 0) > 0 && (
              <button
                onClick={() => readAllMutation.mutate()}
                className="text-[11px] text-teal-400 hover:underline"
              >
                Прочитать все
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {data?.items.length ? (
              data.items.map((n) => (
                <button
                  key={n.id}
                  onClick={() => openNotification(n.id, n.appeal_id)}
                  className={`block w-full border-b border-border/50 px-4 py-3 text-left transition hover:bg-surface ${
                    n.is_read ? 'opacity-60' : ''
                  }`}
                >
                  <p className="text-xs font-medium text-navy-100">{n.title}</p>
                  {n.body && <p className="mt-0.5 line-clamp-2 text-[11px] text-navy-400">{n.body}</p>}
                  <p className="mt-1 text-[10px] text-navy-500">
                    {format(new Date(n.created_at), 'dd MMM HH:mm', { locale: ru })}
                  </p>
                </button>
              ))
            ) : (
              <p className="px-4 py-6 text-center text-xs text-navy-400">Уведомлений нет</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

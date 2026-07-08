import { Navigate, Outlet } from 'react-router-dom'
import type { UserRole } from '../types/common'
import { useAuthContext } from './AuthContext'

const ROLE_LEVEL: Record<UserRole, number> = {
  requester: 0,
  viewer: 1,
  operator: 2,
  analyst: 3,
  admin: 4,
}

/** Доступ только для ролей не ниже minimum; обращавшихся уводит на портал. */
export function RoleRoute({ minimum }: { minimum: UserRole }) {
  const { user } = useAuthContext()
  if (!user) return <Navigate to="/login" replace />
  if (ROLE_LEVEL[user.role] < ROLE_LEVEL[minimum]) {
    return <Navigate to={user.role === 'requester' ? '/my-appeals' : '/dashboard'} replace />
  }
  return <Outlet />
}

import { Navigate, Outlet } from 'react-router-dom'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useAuthContext } from './AuthContext'

export function PrivateRoute() {
  const { user, loading } = useAuthContext()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner label="Проверка сессии…" />
      </div>
    )
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

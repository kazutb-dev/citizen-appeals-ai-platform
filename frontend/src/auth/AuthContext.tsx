import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api } from '../api/client'
import i18n, { SUPPORTED_LANGUAGES, type AppLanguage } from '../i18n'
import type { User } from '../types/common'

export interface RegisterPayload {
  email: string
  password: string
  full_name: string
  requester_type: string
  affiliation?: string
}

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const applyUserLanguage = useCallback((userData: User | null) => {
    const preferred = userData?.preferred_language
    if (!preferred) return
    const lang = preferred.slice(0, 2) as AppLanguage
    if ((SUPPORTED_LANGUAGES as readonly string[]).includes(lang)) {
      void i18n.changeLanguage(lang)
    }
  }, [])

  useEffect(() => {
    api
      .get('/auth/me')
      .then(({ data }) => {
        setUser(data)
        applyUserLanguage(data)
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false))

    const onUnauthorized = () => setUser(null)
    window.addEventListener('ncaip:unauthorized', onUnauthorized)
    return () => window.removeEventListener('ncaip:unauthorized', onUnauthorized)
  }, [applyUserLanguage])

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await api.post('/auth/login', { email, password })
    setUser(data.user)
    applyUserLanguage(data.user)
  }, [applyUserLanguage])

  const register = useCallback(async (payload: RegisterPayload) => {
    const { data } = await api.post('/auth/register', payload)
    setUser(data.user)
    applyUserLanguage(data.user)
  }, [applyUserLanguage])

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      setUser(null)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext(): AuthState {
  return useContext(AuthContext)
}

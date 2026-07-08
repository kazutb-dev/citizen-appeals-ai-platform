import { LogOut } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { LanguageSwitcher } from './LanguageSwitcher'
import { NotificationsBell } from './NotificationsBell'

/** Соответствие базового пути → ключ заголовка в titles.* */
const TITLE_KEYS: Record<string, string> = {
  '/dashboard': 'dashboard',
  '/situation-center': 'situationCenter',
  '/executive': 'executive',
  '/intelligence': 'intelligence',
  '/chief-doctor': 'chiefDoctor',
  '/regional-dashboard': 'regionalDashboard',
  '/integrations': 'integrations',
  '/ai-monitoring': 'aiMonitoring',
  '/appeals': 'appeals',
  '/critical': 'critical',
  '/clusters': 'clusters',
  '/lab': 'lab',
  '/analytics': 'analytics',
  '/regional': 'regional',
  '/requesters': 'requesters',
  '/drafts': 'drafts',
  '/social': 'social',
  '/audit': 'audit',
  '/admin': 'admin',
  '/my-appeals': 'myAppeals',
  '/submit': 'submit',
  '/appeal': 'appeal',
}

export function TopBar() {
  const { user, logout } = useAuth()
  const { t } = useTranslation()
  const location = useLocation()
  const navigate = useNavigate()

  const base = '/' + location.pathname.split('/')[1]
  const titleKey = TITLE_KEYS[base]
  const title = titleKey ? t(`titles.${titleKey}`) : t('common.appName')

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border bg-surface/70 px-6 backdrop-blur">
      <div className="flex items-center gap-2 text-sm">
        <span className="font-semibold text-teal-400">{t('common.appName')}</span>
        <span className="text-navy-500">/</span>
        <span className="font-medium text-navy-100">{title}</span>
      </div>

      <div className="flex items-center gap-4">
        <LanguageSwitcher />
        <NotificationsBell />
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-semibold text-navy-100">{user.full_name}</p>
              <p className="text-xs text-navy-400">{t(`roles.${user.role}`, { defaultValue: user.role })}</p>
            </div>
            <div
              className="flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-navy-900"
              style={{ background: 'var(--gradient-wave)' }}
            >
              {user.full_name.slice(0, 1)}
            </div>
          </div>
        )}
        <button
          onClick={async () => {
            await logout()
            navigate('/login')
          }}
          className="btn-ghost !px-3 !py-2"
          title={t('common.logout')}
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}

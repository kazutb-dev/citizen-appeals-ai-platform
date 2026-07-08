import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Cpu,
  FilePlus2,
  FileText,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  Map,
  MapPin,
  MessageSquare,
  Network,
  Plug,
  ScrollText,
  Settings,
  Share2,
  Sparkles,
  Stethoscope,
  Users,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import logoUrl from '../../assets/logo.svg'
import { fetchOverview } from '../../api/analytics'
import { useAuth } from '../../hooks/useAuth'

interface NavItem {
  path: string
  icon: typeof FileText
  label: string
  badge?: boolean
}

const STAFF_NAVIGATION: NavItem[] = [
  { path: '/situation-center', icon: Activity, label: 'situationCenter' },
  { path: '/intelligence', icon: Gauge, label: 'intelligence' },
  { path: '/executive', icon: Sparkles, label: 'executive' },
  { path: '/chief-doctor', icon: Stethoscope, label: 'chiefDoctor' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'dashboard' },
  { path: '/appeals', icon: FileText, label: 'appeals' },
  { path: '/critical', icon: AlertTriangle, label: 'critical', badge: true },
  { path: '/clusters', icon: Network, label: 'clusters' },
  { path: '/lab', icon: FlaskConical, label: 'lab' },
  { path: '/analytics', icon: BarChart3, label: 'analytics' },
  { path: '/regional', icon: Map, label: 'regional' },
  { path: '/regional-dashboard', icon: MapPin, label: 'regionalDashboard' },
  { path: '/requesters', icon: Users, label: 'requesters' },
  { path: '/drafts', icon: MessageSquare, label: 'drafts' },
  { path: '/social', icon: Share2, label: 'social' },
  { path: '/integrations', icon: Plug, label: 'integrations' },
  { path: '/ai-monitoring', icon: Cpu, label: 'aiMonitoring' },
  { path: '/audit', icon: ScrollText, label: 'audit' },
]

const REQUESTER_NAVIGATION: NavItem[] = [
  { path: '/my-appeals', icon: FileText, label: 'myAppeals' },
  { path: '/submit', icon: FilePlus2, label: 'submit' },
]

export function Sidebar() {
  const { user } = useAuth()
  const { t } = useTranslation()
  const isRequester = user?.role === 'requester'
  const isAdmin = user?.role === 'admin'

  const { data: overview } = useQuery({
    queryKey: ['overview'],
    queryFn: fetchOverview,
    enabled: !isRequester,
  })

  const navigation = isRequester ? REQUESTER_NAVIGATION : STAFF_NAVIGATION

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-border bg-surface/90">
      {/* Logo / brand */}
      <div className="flex items-center gap-3 border-b border-border px-5 py-4">
        <img
          src={logoUrl}
          alt="MedHubHAQ"
          className="h-9 w-9 shrink-0"
        />
        <div>
          <p className="text-sm font-bold tracking-wide text-navy-50">MedHubHAQ</p>
          <p className="text-[10px] uppercase tracking-widest text-navy-400">
            {t('common.tagline')}
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        {navigation.map(({ path, icon: Icon, label, badge }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                isActive
                  ? 'bg-teal-400/10 font-semibold text-teal-400'
                  : 'text-navy-300 hover:bg-surface-card hover:text-navy-100'
              }`
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="flex-1">{t(`nav.${label}`)}</span>
            {badge && (overview?.critical_open ?? 0) > 0 && (
              <span className="rounded-pill bg-risk-critical/20 px-2 py-0.5 font-mono text-[10px] font-semibold text-risk-critical">
                {overview!.critical_open}
              </span>
            )}
          </NavLink>
        ))}

        {isAdmin && (
          <>
            <p className="mt-4 px-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-navy-500">
              {t('nav.management')}
            </p>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-teal-400/10 font-semibold text-teal-400'
                    : 'text-navy-300 hover:bg-surface-card hover:text-navy-100'
                }`
              }
            >
              <Settings className="h-4 w-4 shrink-0" />
              <span>{t('nav.admin')}</span>
            </NavLink>
          </>
        )}
      </nav>

      <div className="border-t border-border px-5 py-3">
        <p className="text-[10px] leading-relaxed text-navy-500">{t('common.orgName')}</p>
      </div>
    </aside>
  )
}

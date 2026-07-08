import { motion } from 'framer-motion'
import { Activity, Heart, Loader2, Shield, Stethoscope } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import logoUrl from '../assets/logo.svg'
import { LanguageSwitcher } from '../components/layout/LanguageSwitcher'
import { useAuth } from '../hooks/useAuth'

const DEMO_ACCOUNTS = [
  { roleKey: 'roles.admin', email: 'admin@medhubhaq.kz' },
  { roleKey: 'roles.analyst', email: 'analyst@medhubhaq.kz' },
  { roleKey: 'roles.operator', email: 'operator@medhubhaq.kz' },
  { roleKey: 'auth.roleDoctor', email: 'doctor@medhubhaq.kz' },
  { roleKey: 'auth.rolePatient', email: 'patient@medhubhaq.kz' },
]

export function LoginPage() {
  const { user, login } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const showDemo =
    (import.meta.env.VITE_ENVIRONMENT ?? import.meta.env.MODE) === 'development'

  if (user) {
    return <Navigate to={user.role === 'requester' ? '/my-appeals' : '/situation-center'} replace />
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email, password)
      navigate('/')
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? t('auth.loginError'))
    } finally {
      setBusy(false)
    }
  }

  const fillDemo = (demoEmail: string, demoPassword: string) => {
    setEmail(demoEmail)
    setPassword(demoPassword)
    setError('')
  }

  const FEATURES = [
    { icon: Stethoscope, text: t('auth.feature1') },
    { icon: Activity, text: t('auth.feature2') },
    { icon: Shield, text: t('auth.feature3') },
    { icon: Heart, text: t('auth.feature4') },
  ]

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--gradient-deep)' }}>
      {/* Left panel — branding */}
      <div className="hidden flex-col justify-between p-10 lg:flex lg:w-[420px] xl:w-[480px]"
           style={{ background: 'rgba(10,26,46,0.7)', borderRight: '1px solid rgba(44,69,101,0.5)' }}>
        <div className="flex items-center gap-3">
          <img src={logoUrl} alt="MedHubHAQ" className="h-10 w-10" />
          <div>
            <p className="text-base font-bold tracking-tight text-white">MedHubHAQ</p>
            <p className="text-[10px] uppercase tracking-widest text-teal-400">Health AI Quality</p>
          </div>
        </div>

        <div className="space-y-6">
          <h2 className="text-3xl font-bold leading-snug text-white">
            {t('auth.brandHeadline')}
          </h2>
          <p className="text-sm leading-relaxed text-navy-300">
            {t('auth.brandSubtitle')}
          </p>

          <div className="space-y-3">
            {FEATURES.map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-400/10">
                  <Icon className="h-4 w-4 text-teal-400" />
                </div>
                <p className="text-sm text-navy-200">{text}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="text-xs text-navy-500">{t('auth.footer')}</p>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 flex-col items-center justify-center px-4 py-8">
        <div className="mb-2 flex w-full max-w-[400px] justify-end">
          <LanguageSwitcher />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-[400px]"
        >
          {/* Mobile logo (hidden on lg) */}
          <div className="mb-8 flex items-center justify-center gap-3 lg:hidden">
            <img src={logoUrl} alt="MedHubHAQ" className="h-10 w-10" />
            <div>
              <p className="text-lg font-bold text-white">MedHubHAQ</p>
              <p className="text-[10px] uppercase tracking-widest text-teal-400">Health AI Quality</p>
            </div>
          </div>

          <div className="mb-6">
            <h1 className="text-2xl font-bold text-navy-50">{t('auth.loginTitle')}</h1>
            <p className="mt-1 text-sm text-navy-400">{t('auth.loginSubtitle')}</p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-navy-400">
                {t('auth.email')}
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input w-full"
                placeholder="user@medhubhaq.kz"
                autoComplete="username"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-navy-400">
                {t('auth.password')}
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input w-full"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>
            {error && (
              <p className="rounded-md border border-risk-critical/40 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
                {error}
              </p>
            )}
            <button type="submit" disabled={busy} className="btn-primary w-full justify-center py-3 text-sm font-semibold">
              {busy && <Loader2 className="h-4 w-4 animate-spin" />}
              {busy ? t('auth.loggingIn') : t('auth.loginButton')}
            </button>
            <p className="text-center text-xs text-navy-400">
              {t('auth.registerPrompt')}{' '}
              <Link to="/register" className="text-teal-400 hover:text-teal-300 hover:underline">
                {t('auth.registerLink')}
              </Link>
            </p>
          </form>

          {/* Demo credentials */}
          {showDemo && (
            <div className="mt-6 rounded-xl border border-teal-400/20 bg-teal-400/5 p-4">
              <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-teal-400">
                {t('auth.demoHint')}
              </p>
              <div className="space-y-1.5">
                {DEMO_ACCOUNTS.map(({ roleKey, email: demoEmail }) => (
                  <button
                    key={demoEmail}
                    type="button"
                    onClick={() => fillDemo(demoEmail, 'password')}
                    className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs transition hover:bg-teal-400/10"
                  >
                    <span className="font-semibold text-navy-200">{t(roleKey)}</span>
                    <span className="font-mono text-navy-400">{demoEmail}</span>
                  </button>
                ))}
              </div>
              <p className="mt-2 text-[10px] text-navy-500">
                {t('auth.demoPasswords')} <span className="font-mono text-navy-300">password</span>
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}


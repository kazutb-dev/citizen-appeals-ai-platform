import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import logoUrl from '../assets/logo.svg'
import { LanguageSwitcher } from '../components/layout/LanguageSwitcher'
import { useLabels, REQUESTER_TYPE_KEYS } from '../i18n/labels'
import { useAuth } from '../hooks/useAuth'

export function RegisterPage() {
  const { user, register } = useAuth()
  const { t } = useTranslation()
  const labels = useLabels()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    requester_type: 'patient',
    affiliation: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) {
    return <Navigate to={user.role === 'requester' ? '/my-appeals' : '/dashboard'} replace />
  }

  const set = (key: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [key]: e.target.value })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await register({ ...form, affiliation: form.affiliation || undefined })
      navigate('/my-appeals')
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? t('auth.registerError'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="flex min-h-screen items-center justify-center px-4"
      style={{ background: 'var(--gradient-deep)' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md"
      >
        <div className="mb-2 flex justify-end">
          <LanguageSwitcher />
        </div>
        <div className="mb-6 text-center">
          <img
            src={logoUrl}
            alt="MedHubHAQ"
            className="mx-auto mb-4 h-14 w-14"
          />
          <h1 className="text-xl font-bold tracking-tight text-navy-50">{t('auth.registerPortalTitle')}</h1>
          <p className="mt-1 text-sm text-navy-300">{t('common.orgName')}</p>
        </div>

        <form onSubmit={submit} className="card space-y-4 p-6">
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-navy-400">{t('auth.fullName')}</label>
            <input required minLength={3} value={form.full_name} onChange={set('full_name')} className="input w-full" placeholder={t('auth.fullNamePlaceholder')} />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-navy-400">{t('auth.email')}</label>
            <input type="email" required value={form.email} onChange={set('email')} className="input w-full" placeholder="user@medhubhaq.kz" autoComplete="username" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-navy-400">{t('auth.passwordMin')}</label>
            <input type="password" required minLength={8} value={form.password} onChange={set('password')} className="input w-full" autoComplete="new-password" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-navy-400">{t('auth.whoAreYou')}</label>
              <select value={form.requester_type} onChange={set('requester_type')} className="input w-full">
                {REQUESTER_TYPE_KEYS.map((k) => (
                  <option key={k} value={k}>{labels.requesterType(k)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-navy-400">{t('auth.regionOrg')}</label>
              <input value={form.affiliation} onChange={set('affiliation')} className="input w-full" placeholder={t('auth.optional')} />
            </div>
          </div>
          {error && (
            <p className="rounded-md border border-risk-critical/40 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
              {error}
            </p>
          )}
          <button type="submit" disabled={busy} className="btn-primary w-full justify-center">
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            {busy ? t('auth.registering') : t('auth.registerButton')}
          </button>
          <p className="text-center text-xs text-navy-400">
            {t('auth.haveAccount')}{' '}
            <Link to="/login" className="text-teal-400 hover:text-teal-300 hover:underline">{t('auth.loginLink')}</Link>
          </p>
        </form>
      </motion.div>
    </div>
  )
}

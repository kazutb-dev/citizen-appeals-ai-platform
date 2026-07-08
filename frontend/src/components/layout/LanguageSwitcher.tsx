import { Globe } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES } from '../../i18n'
import type { AppLanguage } from '../../i18n'

const FLAGS: Record<AppLanguage, string> = { kk: '🇰🇿', ru: '🇷🇺', en: '🇺🇸' }
const LABELS: Record<AppLanguage, string> = { kk: 'Қазақша', ru: 'Русский', en: 'English' }

export function LanguageSwitcher() {
  const { i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const current = (SUPPORTED_LANGUAGES as readonly string[]).includes(i18n.resolvedLanguage ?? '')
    ? (i18n.resolvedLanguage as AppLanguage)
    : 'ru'

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  const select = (lng: AppLanguage) => {
    i18n.changeLanguage(lng)
    setOpen(false)
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="btn-ghost !px-2.5 !py-2"
        title={LABELS[current]}
        aria-label="Language"
      >
        <Globe className="h-4 w-4" />
        <span className="text-sm">{FLAGS[current]}</span>
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-2 w-40 overflow-hidden rounded-lg border border-border bg-surface-card shadow-xl">
          {SUPPORTED_LANGUAGES.map((lng) => (
            <button
              key={lng}
              onClick={() => select(lng)}
              className={`flex w-full items-center gap-2.5 px-3 py-2.5 text-sm transition-colors ${
                lng === current
                  ? 'bg-teal-400/10 font-semibold text-teal-400'
                  : 'text-navy-200 hover:bg-surface'
              }`}
            >
              <span className="text-base">{FLAGS[lng]}</span>
              <span>{LABELS[lng]}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

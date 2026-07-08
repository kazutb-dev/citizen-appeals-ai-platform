import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'

import en from './locales/en.json'
import kk from './locales/kk.json'
import ru from './locales/ru.json'

export const SUPPORTED_LANGUAGES = ['kk', 'ru', 'en'] as const
export type AppLanguage = (typeof SUPPORTED_LANGUAGES)[number]

/** Cookie/localStorage key — читается также бэкендом для генерации AI-ответов
 * на выбранном языке (см. app.core.i18n.resolve_language). */
export const LANGUAGE_STORAGE_KEY = 'medhub_lang'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      kk: { translation: kk },
      ru: { translation: ru },
      en: { translation: en },
    },
    fallbackLng: 'ru',
    supportedLngs: SUPPORTED_LANGUAGES as unknown as string[],
    nonExplicitSupportedLngs: true,
    load: 'languageOnly',
    detection: {
      order: ['localStorage', 'cookie', 'navigator', 'htmlTag'],
      caches: ['localStorage', 'cookie'],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
      lookupCookie: LANGUAGE_STORAGE_KEY,
      cookieMinutes: 60 * 24 * 365,
    },
    interpolation: { escapeValue: false },
    returnNull: false,
  })

/** Держит атрибут <html lang> в актуальном состоянии для доступности и SEO. */
function syncHtmlLang(lng: string) {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = lng
  }
}
syncHtmlLang(i18n.resolvedLanguage ?? 'ru')
i18n.on('languageChanged', syncHtmlLang)

export default i18n

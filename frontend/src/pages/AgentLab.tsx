import { motion } from 'framer-motion'
import { FlaskConical, Rocket } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { startLabAnalysis, subscribeLabStream } from '../api/lab'
import type { LabEvent } from '../api/lab'
import { AgentPanel, reduceLabEvents } from '../components/agents/AgentPanel'
import { useCategoryOptions } from '../i18n/labels'

const REGIONS = [
  'Астана', 'Алматы', 'Шымкент', 'Карагандинская область', 'Туркестанская область',
  'Восточно-Казахстанская область', 'Актюбинская область', 'Павлодарская область', 'Онлайн / дистанционно',
]

const EXAMPLES: { labelKey: string; text: string; category: string }[] = [
  {
    labelKey: 'lab.exampleCampaign',
    category: 'medicines',
    text: 'В поликлинике снова нет льготных лекарств для диабетиков! Инсулин не выдают уже неделю. Требуем немедленно решить проблему — так нельзя!',
  },
  {
    labelKey: 'lab.exampleOutbreak',
    category: 'sanitary',
    text: 'В отделении массово заболели пациенты с признаками кишечной инфекции. Подозреваем нарушение санитарных норм. Прошу срочно провести проверку.',
  },
  {
    labelKey: 'lab.exampleCritical',
    category: 'emergency',
    text: 'Скорая ехала более двух часов к пожилому человеку с сердечным приступом, а в приёмном отделении отказали в госпитализации. Состояние тяжёлое, есть угроза жизни.',
  },
]

export function AgentLab() {
  const { t } = useTranslation()
  const categoryOptions = useCategoryOptions()
  const [text, setText] = useState('')
  const [region, setRegion] = useState(REGIONS[0])
  const [category, setCategory] = useState('other')
  const [events, setEvents] = useState<LabEvent[]>([])
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const unsubscribe = useRef<(() => void) | null>(null)

  useEffect(() => () => unsubscribe.current?.(), [])

  const run = async () => {
    if (text.trim().length < 10) {
      setError(t('lab.minLength'))
      return
    }
    setError('')
    setEvents([])
    setRunning(true)
    try {
      const { task_id } = await startLabAnalysis({ text, region, category })
      unsubscribe.current = subscribeLabStream(
        task_id,
        (event) => {
          setEvents((prev) => [...prev, event])
          if (event.agent === 'orchestrator' && event.status === 'error') {
            setError(String(event.payload?.detail ?? t('lab.analysisError')))
          }
        },
        () => setRunning(false),
      )
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? t('lab.startError'))
      setRunning(false)
    }
  }

  const state = reduceLabEvents(events)

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/15 text-teal-400">
            <FlaskConical className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-navy-50">{t('lab.title')}</h1>
            <p className="text-xs text-navy-400">
              {t('lab.subtitle')}
            </p>
          </div>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          placeholder={t('lab.placeholder')}
          className="input w-full resize-y font-normal leading-relaxed"
        />

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <select value={region} onChange={(e) => setRegion(e.target.value)} className="input">
            {REGIONS.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="input">
            {categoryOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.labelKey}
              onClick={() => {
                setText(ex.text)
                setCategory(ex.category)
              }}
              className="rounded-full border border-border px-3 py-1.5 text-xs text-navy-300 transition hover:border-accent hover:text-teal-400"
            >
              {t(ex.labelKey)}
            </button>
          ))}
        </div>

        {error && (
          <p className="mt-3 rounded-lg border border-risk-critical/40 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
            {error}
          </p>
        )}

        <motion.button
          whileTap={{ scale: 0.98 }}
          onClick={run}
          disabled={running}
          className="btn-primary mt-4 w-full justify-center !py-3 text-base shadow-glow"
        >
          <Rocket className="h-5 w-5" />
          {running ? t('lab.running') : t('lab.run')}
        </motion.button>
      </motion.div>

      {(events.length > 0 || running) && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card p-6">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-navy-400">
            {t('lab.results')}
          </h2>
          <AgentPanel state={state} />
        </motion.div>
      )}
    </div>
  )
}

import { useMutation, useQuery } from '@tanstack/react-query'
import { Loader2, Paperclip, Send, X } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { submitAppeal, uploadAttachment } from '../api/appeals'
import { fetchCategories, fetchLocations } from '../api/meta'
import { LocationPicker, type LocationValue } from '../components/appeals/LocationPicker'
import { useLabels } from '../i18n/labels'
import { regionCenter } from '../lib/kzGeo'

const MAX_FILES = 5

export function SubmitAppeal() {
  const { t } = useTranslation()
  const labels = useLabels()
  const navigate = useNavigate()
  const { data: categories } = useQuery({ queryKey: ['meta-categories'], queryFn: fetchCategories })
  const { data: locations } = useQuery({ queryKey: ['meta-locations'], queryFn: fetchLocations })

  const [form, setForm] = useState({
    title: '',
    text: '',
    category: '',
    subcategory: '',
    region: '',
    district: '',
  })
  const [files, setFiles] = useState<File[]>([])
  const [location, setLocation] = useState<LocationValue | null>(null)
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: async () => {
      const appeal = await submitAppeal({
        title: form.title,
        text: form.text,
        category: form.category,
        subcategory: form.subcategory || undefined,
        region: form.region,
        district: form.district || undefined,
        latitude: location!.lat,
        longitude: location!.lng,
        location_name: location?.name || form.region || undefined,
      })
      for (const file of files) {
        await uploadAttachment(appeal.id, file)
      }
      return appeal
    },
    onSuccess: (appeal) => navigate(`/appeal/${appeal.id}`),
    onError: (err: any) =>
      setError(err?.response?.data?.detail ?? t('submitForm.submitError')),
  })

  const subcategories = form.category && categories
    ? Object.entries(categories[form.category]?.subcategories ?? {})
    : []

  const addFiles = (list: FileList | null) => {
    if (!list) return
    setFiles((prev) => [...prev, ...Array.from(list)].slice(0, MAX_FILES))
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div>
        <h1 className="text-lg font-semibold text-navy-50">{t('titles.submit')}</h1>
        <p className="mt-1 text-sm text-navy-400">
          {t('submitForm.subtitle')}
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          setError('')
          if (!location) {
            setError(t('submitForm.locationRequired'))
            return
          }
          mutation.mutate()
        }}
        className="card space-y-4 p-6"
      >
        <div>
          <label className="mb-1.5 block text-xs font-medium text-navy-300">{t('submitForm.titleLabel')}</label>
          <input
            required
            minLength={3}
            maxLength={500}
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="input w-full"
            placeholder={t('submitForm.titlePlaceholder')}
          />
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">{t('submitForm.categoryLabel')}</label>
            <select
              required
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value, subcategory: '' })}
              className="input w-full"
            >
              <option value="">{t('submitForm.categoryPlaceholder')}</option>
              {categories &&
                Object.entries(categories).map(([key, group]) => (
                  <option key={key} value={key}>{labels.category(key) || group.label}</option>
                ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">{t('submitForm.subcategoryLabel')}</label>
            <select
              value={form.subcategory}
              onChange={(e) => setForm({ ...form, subcategory: e.target.value })}
              className="input w-full"
              disabled={!subcategories.length}
            >
              <option value="">{subcategories.length ? t('submitForm.subcategoryPlaceholder') : '—'}</option>
              {subcategories.map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">{t('submitForm.regionLabel')}</label>
            <select
              required
              value={form.region}
              onChange={(e) => {
                const region = e.target.value
                setForm({ ...form, region })
                setLocation((prev) => {
                  if (prev) return prev
                  const [lat, lng] = regionCenter(region)
                  return { lat, lng, name: region }
                })
              }}
              className="input w-full"
            >
              <option value="">{t('submitForm.regionPlaceholder')}</option>
              {locations?.map((loc) => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-navy-300">{t('submitForm.districtLabel')}</label>
            <input
              value={form.district}
              onChange={(e) => setForm({ ...form, district: e.target.value })}
              className="input w-full"
              placeholder={t('submitForm.optional')}
            />
          </div>
        </div>

        <LocationPicker value={location} onChange={setLocation} />

        <div>
          <label className="mb-1.5 block text-xs font-medium text-navy-300">{t('submitForm.textLabel')}</label>
          <textarea
            required
            minLength={10}
            maxLength={20000}
            rows={8}
            value={form.text}
            onChange={(e) => setForm({ ...form, text: e.target.value })}
            className="input w-full resize-y"
            placeholder={t('submitForm.textPlaceholder')}
          />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-navy-300">
            {t('submitForm.attachmentsLabel', { max: MAX_FILES })}
          </label>
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border px-4 py-3 text-sm text-navy-300 transition hover:border-border-light hover:text-navy-100">
            <Paperclip className="h-4 w-4" />
            {t('submitForm.attachFiles')}
            <input
              type="file"
              multiple
              className="hidden"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg,.txt"
              onChange={(e) => addFiles(e.target.files)}
            />
          </label>
          {files.length > 0 && (
            <ul className="mt-2 space-y-1">
              {files.map((f, i) => (
                <li key={`${f.name}-${i}`} className="flex items-center gap-2 text-xs text-navy-200">
                  <Paperclip className="h-3 w-3 text-navy-400" />
                  {f.name}
                  <span className="text-navy-500">({Math.round(f.size / 1024)} {t('submitForm.kb')})</span>
                  <button
                    type="button"
                    onClick={() => setFiles(files.filter((_, j) => j !== i))}
                    className="text-navy-400 hover:text-risk-critical"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && (
          <p className="rounded-lg border border-risk-critical/40 bg-risk-critical/10 px-3 py-2 text-xs text-risk-critical">
            {error}
          </p>
        )}

        <button type="submit" disabled={mutation.isPending || !location} className="btn-primary w-full justify-center">
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          {t('submitForm.submit')}
        </button>
      </form>
    </div>
  )
}
